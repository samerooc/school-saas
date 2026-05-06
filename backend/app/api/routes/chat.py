"""Chat / Messaging API - Module 5"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db, AsyncSessionLocal
from app.core.security import get_current_user_payload, decode_access_token
from app.models.models import User

router = APIRouter(prefix="/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}
    async def connect(self, ws: WebSocket, uid: str):
        await ws.accept()
        self.active.setdefault(uid, []).append(ws)
    def disconnect(self, ws: WebSocket, uid: str):
        if uid in self.active:
            self.active[uid] = [w for w in self.active[uid] if w != ws]
            if not self.active[uid]: del self.active[uid]
    async def send(self, uid: str, msg: dict):
        for ws in self.active.get(uid, []):
            try: await ws.send_json(msg)
            except: pass
    def is_online(self, uid: str) -> bool:
        return bool(self.active.get(uid))

manager = ConnectionManager()
_messages: List[dict] = []

@router.get("/conversations")
async def conversations(db: AsyncSession = Depends(get_db), payload: dict = Depends(get_current_user_payload)):
    uid, sid = payload["sub"], payload["school_id"]
    my = [m for m in _messages if m["sender_id"] == uid or m["receiver_id"] == uid]
    pids = {m["sender_id"] if m["sender_id"] != uid else m["receiver_id"] for m in my} - {uid}
    result = []
    for pid in pids:
        p = (await db.execute(select(User).where(User.id == pid, User.school_id == sid))).scalar_one_or_none()
        if not p: continue
        cm = [m for m in my if m["sender_id"] == pid or m["receiver_id"] == pid]
        result.append({"partner_id": str(pid), "partner_name": p.full_name, "partner_role": p.role,
                        "last_message": cm[-1]["text"] if cm else None,
                        "unread_count": sum(1 for m in cm if m["receiver_id"] == uid and not m.get("read")),
                        "is_online": manager.is_online(str(pid))})
    return sorted(result, key=lambda x: x["last_message"] or "", reverse=True)

@router.get("/messages/{partner_id}")
async def get_messages(partner_id: str, payload: dict = Depends(get_current_user_payload)):
    uid = payload["sub"]
    msgs = sorted([m for m in _messages if (m["sender_id"]==uid and m["receiver_id"]==partner_id) or (m["sender_id"]==partner_id and m["receiver_id"]==uid)], key=lambda x: x["created_at"])
    for m in msgs:
        if m["receiver_id"] == uid: m["read"] = True
    return {"messages": msgs[-50:], "total": len(msgs)}

@router.post("/messages/{receiver_id}", status_code=201)
async def send_message(receiver_id: str, text: str, db: AsyncSession = Depends(get_db), payload: dict = Depends(get_current_user_payload)):
    sid = payload["school_id"]
    if not (await db.execute(select(User).where(User.id == receiver_id, User.school_id == sid))).scalar_one_or_none():
        raise HTTPException(404, "Recipient not found")
    if not text.strip() or len(text) > 1000: raise HTTPException(400, "Invalid message")
    msg = {"id": str(uuid.uuid4()), "sender_id": payload["sub"], "receiver_id": receiver_id, "text": text.strip(), "read": False, "created_at": datetime.now(timezone.utc).isoformat()}
    _messages.append(msg)
    await manager.send(receiver_id, {"type": "new_message", "message": msg})
    return {"id": msg["id"]}

@router.websocket("/ws")
async def ws_chat(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
        uid, sid = payload["sub"], payload["school_id"]
    except:
        await websocket.close(code=4001); return
    await manager.connect(websocket, uid)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                rid, text = data.get("receiver_id"), (data.get("text") or "").strip()
                if not rid or not text or len(text) > 1000: continue
                async with AsyncSessionLocal() as db:
                    if not (await db.execute(select(User).where(User.id == rid, User.school_id == sid))).scalar_one_or_none(): continue
                msg = {"id": str(uuid.uuid4()), "sender_id": uid, "receiver_id": rid, "text": text, "read": False, "created_at": datetime.now(timezone.utc).isoformat()}
                _messages.append(msg)
                await manager.send(uid, {"type": "message_sent", "message": msg})
                await manager.send(rid, {"type": "new_message", "message": msg})
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, uid)
