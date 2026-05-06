"""
Push Notifications API - Module 5
FCM token registration + send notifications
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import require_roles, get_current_user_payload
from app.models.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Store FCM tokens in memory (add fcm_tokens table to DB in production)
_fcm_tokens: dict = {}  # user_id -> fcm_token


@router.post("/register-token")
async def register_fcm_token(
    fcm_token: str,
    payload: dict = Depends(get_current_user_payload),
):
    """Mobile app calls this after login to register FCM token"""
    user_id = payload["sub"]
    _fcm_tokens[user_id] = fcm_token
    return {"message": "Token registered"}


@router.post("/send")
async def send_notification(
    title: str,
    body: str,
    target_user_id: Optional[str] = None,
    target_role: Optional[str] = None,
    route: Optional[str] = None,  # Deep link: fee_reminder, attendance_alert etc.
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    """
    Send push notification to specific user or all users with a role.
    Uses Firebase Admin SDK.
    """
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        from app.core.config import settings

        # Init Firebase (once)
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)

    except ImportError:
        raise HTTPException(500, "firebase-admin not installed. Run: pip install firebase-admin")
    except Exception as e:
        raise HTTPException(500, f"Firebase init failed: {e}")

    school_id = payload["school_id"]
    tokens_to_notify = []

    if target_user_id:
        token = _fcm_tokens.get(target_user_id)
        if token:
            tokens_to_notify.append(token)
    elif target_role:
        # Get all users with this role in the school
        result = await db.execute(
            select(User).where(User.school_id == school_id, User.role == target_role, User.is_active == True)
        )
        users = result.scalars().all()
        for user in users:
            token = _fcm_tokens.get(str(user.id))
            if token:
                tokens_to_notify.append(token)

    if not tokens_to_notify:
        return {"message": "No registered devices found", "sent": 0}

    # Send via FCM
    sent = 0
    for token in tokens_to_notify:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={"route": route or "", "title": title, "body": body},
                token=token,
                android=messaging.AndroidConfig(priority="high"),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default", badge=1)
                    )
                ),
            )
            messaging.send(message)
            sent += 1
        except Exception:
            pass  # Invalid/expired token — ignore

    return {"message": f"Sent to {sent} devices", "sent": sent, "total_tokens": len(tokens_to_notify)}
