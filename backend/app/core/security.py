from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID

import bcrypt
import jwt
from jwt import PyJWTError

from app.core.config import settings

JWT_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt for storage in
    users.password_hash. bcrypt only uses the first 72 bytes of the
    input, so longer passwords are truncated rather than raising."""
    pw_bytes = plain_password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    pw_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(pw_bytes, password_hash.encode("utf-8"))


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def create_access_token(
    user_id: Union[UUID, str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Encode a JWT carrying the user id as `sub` plus an expiry claim.

    Defaults to JWT_EXPIRE_MINUTES from settings when expires_delta isn't
    given. The next prompt's login route calls this after verifying the
    user's password.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT. Returns the payload dict (with `sub` as
    the user id string) on success, or None if the token is invalid or
    expired. Callers (e.g. an auth dependency in the next prompt) decide
    how to turn a None into a 401.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except PyJWTError:
        return None
