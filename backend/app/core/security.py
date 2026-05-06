"""
JWT Authentication using RS256 (asymmetric keys)
WHY RS256: If frontend ever needs to verify tokens independently,
it can use the PUBLIC key only — private key never leaves the server.
"""
import os, uuid, hashlib, secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# Password hashing — bcrypt cost=12 (slow enough to resist brute force)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
bearer_scheme = HTTPBearer(auto_error=False)

# Load RSA keys once at startup
def _load_key(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Key not found: {path}\n"
            "Run: openssl genrsa -out keys/private.pem 2048\n"
            "     openssl rsa -in keys/private.pem -pubout -out keys/public.pem"
        )
    return open(path).read()

_PRIVATE_KEY: Optional[str] = None
_PUBLIC_KEY: Optional[str] = None

def get_private_key() -> str:
    global _PRIVATE_KEY
    if _PRIVATE_KEY is None:
        _PRIVATE_KEY = _load_key(settings.JWT_PRIVATE_KEY_PATH)
    return _PRIVATE_KEY

def get_public_key() -> str:
    global _PUBLIC_KEY
    if _PUBLIC_KEY is None:
        _PUBLIC_KEY = _load_key(settings.JWT_PUBLIC_KEY_PATH)
    return _PUBLIC_KEY


# ── Password utilities ──────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    # Uses constant-time comparison internally — prevents timing attacks
    return pwd_context.verify(plain, hashed)

def validate_password_strength(password: str) -> bool:
    """Min 8 chars, 1 upper, 1 digit, 1 special"""
    import re
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
        "jti": str(uuid.uuid4()),   # unique token ID for blacklisting
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, get_private_key(), algorithm="RS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, get_public_key(), algorithms=["RS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        # Generic message — never reveal WHY token failed (timing/info leak)
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Refresh Token ───────────────────────────────────────────────────────────

def generate_refresh_token() -> tuple[str, str]:
    """
    Returns (raw_token, hashed_token)
    raw_token  → sent to client in HttpOnly cookie
    hashed_token → stored in DB (never store raw)
    WHY: Even if DB is compromised, attacker cannot use hashed token
    """
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
