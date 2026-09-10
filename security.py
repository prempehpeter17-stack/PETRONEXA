"""Password hashing and JWT helpers."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from config import settings

ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if "$" not in hashed_password or hashed_password.startswith("$"):
            return False
        salt_hex, hash_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        new_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, 100_000)
        return hmac.compare_digest(new_hash, expected_hash)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{salt.hex()}${hash_bytes.hex()}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret, algorithm=ALGORITHM)
