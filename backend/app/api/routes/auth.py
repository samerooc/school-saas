"""
Authentication Routes — All tokens validated server-side
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, EmailStr, field_validator

from app.db.session import get_db
from app.models.models import User, RefreshToken, AuditLog
from app.core.security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, generate_refresh_token, hash_refresh_token,
    get_current_user_payload
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 30


# ── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    school_id: str
    full_name: str
    email: EmailStr
    password: str
    role: str = "student"

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                "Password must be 8+ chars with uppercase, number, and special character"
            )
        return v

    @field_validator("role")
    @classmethod
    def check_role(cls, v):
        allowed = ["admin", "teacher", "student", "parent", "principal"]
        if v not in allowed:
            raise ValueError(f"Role must be one of: {allowed}")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    full_name: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_refresh_cookie(response: Response, token: str):
    """
    HttpOnly + Secure + SameSite=Strict
    WHY: JS cannot read this cookie — blocks XSS token theft
    """
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.is_production,  # HTTPS only in prod
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/auth",               # Only sent to auth routes
    )


async def _log_audit(db, school_id, user_id, action, request: Request):
    log = AuditLog(
        school_id=school_id,
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    # 1. Check lockout FIRST — prevent timing oracle
    result = await db.execute(select(User).where(User.email == body.email))
    user: Optional[User] = result.scalar_one_or_none()

    # Always run a dummy check to prevent user enumeration via timing
    if user is None:
        verify_password("dummy", "$2b$12$dummyhash000000000000000000000000000000000000000000000")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # 2. Check lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
        raise HTTPException(
            status_code=423,
            detail=f"Account locked. Try again in {remaining} minutes."
        )

    # 3. Verify password
    if not verify_password(body.password, user.password_hash):
        new_attempts = user.failed_login_attempts + 1
        updates = {"failed_login_attempts": new_attempts}
        if new_attempts >= MAX_FAILED_ATTEMPTS:
            updates["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        await db.execute(update(User).where(User.id == user.id).values(**updates))
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    # 4. Reset failed attempts, update last login
    await db.execute(
        update(User).where(User.id == user.id).values(
            failed_login_attempts=0,
            locked_until=None,
            last_login=datetime.now(timezone.utc),
        )
    )

    # 5. Generate tokens
    access_token = create_access_token(
        str(user.id), str(user.school_id), user.role
    )
    raw_refresh, hashed_refresh = generate_refresh_token()
    family_id = str(uuid.uuid4())

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh,
        family_id=family_id,
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)

    await _log_audit(db, user.school_id, user.id, "user.login", request)

    _set_refresh_cookie(response, raw_refresh)

    return TokenResponse(
        access_token=access_token,
        role=user.role,
        user_id=str(user.id),
        full_name=user.full_name,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Read refresh token from HttpOnly cookie only.
    Implements rotation — old token revoked, new one issued.
    If old token reused (theft detection) → revoke entire family.
    """
    raw = request.cookies.get("refresh_token")
    if not raw:
        raise HTTPException(status_code=401, detail="No refresh token")

    token_hash = hash_refresh_token(raw)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt: Optional[RefreshToken] = result.scalar_one_or_none()

    if rt is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Reuse detection — if already revoked, someone is using a stolen token
    if rt.is_revoked:
        # Revoke entire family (compromise response)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == rt.family_id)
            .values(is_revoked=True)
        )
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=401, detail="Token reuse detected. Please login again.")

    if rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Get user
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user: Optional[User] = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Revoke old token
    await db.execute(
        update(RefreshToken).where(RefreshToken.id == rt.id).values(is_revoked=True)
    )

    # Issue new tokens
    access_token = create_access_token(str(user.id), str(user.school_id), user.role)
    new_raw, new_hash = generate_refresh_token()

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        family_id=rt.family_id,   # Same family for theft tracking
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_rt)

    _set_refresh_cookie(response, new_raw)

    return TokenResponse(
        access_token=access_token,
        role=user.role,
        user_id=str(user.id),
        full_name=user.full_name,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    raw = request.cookies.get("refresh_token")
    if raw:
        token_hash = hash_refresh_token(raw)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True)
        )

    response.delete_cookie("refresh_token", path="/api/auth")
    await _log_audit(db, payload.get("school_id"), payload.get("sub"), "user.logout", request)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "school_id": str(user.school_id),
        "is_premium": False,  # Populated from student record if role=student
        "must_change_password": user.must_change_password,
    }
