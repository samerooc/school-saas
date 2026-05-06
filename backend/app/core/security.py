"""
JWT Authentication — RS256 if keys exist, HS256 fallback via SECRET_KEY
"""
import os, uuid, hashlib, secrets, re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
bearer_scheme = HTTPBearer(auto_error=False)

_PRIVATE_KEY: Optional[str] = None
_PUBLIC_KEY: Optional[str] = None
_USE_RSA: Optional[bool] = None


def _detect_mode() -> bool:
    """Returns True if RSA keys exist, False = use HS256 with SECRET_KEY"""
    global _USE_RSA
    if _USE_RSA is None:
        priv = settings.JWT_PRIVATE_KEY_PATH
        pub = settings.JWT_PUBLIC_KEY_PATH
        _USE_RSA = os.path.exists(priv) and os.path.exists(pub)
        mode = "RS256 (RSA keys)" if _USE_RSA else "HS256 (SECRET_KEY fallback)"
        print(f"🔑 JWT mode: {mode}")
    return _USE_RSA


def get_private_key() -> str:
    global _PRIVATE_KEY
    if _PRIVATE_KEY is None:
        if _detect_mode():
            _PRIVATE_KEY = open(settings.JWT_PRIVATE_KEY_PATH).read()
        else:
            _PRIVATE_KEY = settings.SECRET_KEY
    return _PRIVATE_KEY


def get_public_key() -> str:
    global _PUBLIC_KEY
    if _PUBLIC_KEY is None:
        if _detect_mode():
            _PUBLIC_KEY = open(settings.JWT_PUBLIC_KEY_PATH).read()
        else:
            _PUBLIC_KEY = settings.SECRET_KEY
    return _PUBLIC_KEY


def _algo() -> str:
    return "RS256" if _detect_mode() else "HS256"


# ── Password utilities ──────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def validate_password_strength(password: str) -> bool:
    """Min 8 chars, 1 upper, 1 digit, 1 special"""
    return bool(re.match(
        r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$',
        password
    ))


# ── Access Token ────────────────────────────────────────────────────────────

def create_access_token(user_id: str, school_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "school_id": str(school_id),
        "role": role,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, get_private_key(), algorithm=_algo())


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, get_public_key(), algorithms=[_algo()])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Refresh Token ───────────────────────────────────────────────────────────

def generate_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed

def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ── FastAPI Dependencies ────────────────────────────────────────────────────

async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_access_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    Usage: Depends(require_roles("admin", "principal"))
    """
    async def _check(
        payload: Dict = Depends(get_current_user_payload)
    ) -> Dict:
        if payload.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this resource"
            )
        return payload
    return _check
