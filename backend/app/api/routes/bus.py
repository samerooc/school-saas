"""Bus GPS Tracking API - Module 5"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from app.core.security import require_roles, get_current_user_payload, decode_access_token

router = APIRouter(prefix="/bus", tags=["bus"])
_buses: Dict[str, dict] = {}
_locations: Dict[str, dict] = {}
_watchers: Dict[str, List[WebSocket]] = {}

@router.post("/routes", status_code=201)
async def create_bus(route_name: str, vehicle_number: str, driver_name: str, driver_phone: str,
                     payload: dict = Depends(require_roles("admin"))):
    bid = str(uuid.uuid4())
    _buses[bid] = {"id": bid, "school_id": payload["school_id"], "route_name": route_name,
                   "vehicle_number": vehicle_number, "driver_name": driver_name, "driver_phone": driver_phone}
    return {"id": bid, "message": "Bus route created"}

@router.get("/routes")
async def list_buses(payload: dict = Depends(get_current_user_payload)):
    sid = payload["school_id"]
    buses = [b for b in _buses.values() if b["school_id"] == sid]
    for bus in buses:
        loc = _locations.get(bus["id"])
        bus["current_location"] = loc
        bus["is_online"] = bool(loc and (datetime.now(timezone.utc).timestamp() - datetime.fromisoformat(loc["updated_at"]).timestamp() < 300))
    return buses

@router.post("/location/{bus_id}")
async def update_location(bus_id: str, lat: float, lng: float, speed: Optional[float] = None,
                          payload: dict = Depends(require_roles("teacher", "admin"))):
    if bus_id not in _buses: raise HTTPException(404, "Bus not found")
    loc = {"bus_id": bus_id, "lat": lat, "lng": lng, "speed": speed or 0, "updated_at": datetime.now(timezone.utc).isoformat()}
    _locations[bus_id] = loc
    dead = []
    for ws in _watchers.get(bus_id, []):
        try: await ws.send_json({"type": "location_update", "location": loc})
        except: dead.append(ws)
    for ws in dead: _watchers.get(bus_id, []).remove(ws)
    return {"ok": True}

@router.get("/location/{bus_id}")
async def get_location(bus_id: str, payload: dict = Depends(get_current_user_payload)):
    loc = _locations.get(bus_id)
    return {"bus_id": bus_id, "location": loc, "status": "online" if loc else "offline"}

@router.websocket("/track/{bus_id}")
async def track_bus(websocket: WebSocket, bus_id: str, token: str = Query(...)):
    try: decode_access_token(token)
    except: await websocket.close(code=4001); return
    await websocket.accept()
    _watchers.setdefault(bus_id, []).append(websocket)
    await websocket.send_json({"type": "initial_location", "location": _locations.get(bus_id)})
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping": await websocket.send_text("pong")
    except WebSocketDisconnect:
        if bus_id in _watchers and websocket in _watchers[bus_id]:
            _watchers[bus_id].remove(websocket)
