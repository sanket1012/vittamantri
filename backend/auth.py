import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Optional

import jwt
from flask import g, jsonify, request

logger = logging.getLogger("vittamantri.auth")

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = _DATA_DIR / "users.json"

_JWT_SECRET = os.getenv("JWT_SECRET", "")
_TOKEN_EXPIRY_DAYS = 30


def load_users() -> list[dict]:
    if not USERS_FILE.exists():
        return []
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to load users.json")
        return []


def save_users(users: list[dict]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def get_user_by_id(user_id: int) -> Optional[dict]:
    return next((u for u in load_users() if u["id"] == user_id), None)


def get_user_by_username(username: str) -> Optional[dict]:
    return next((u for u in load_users() if u["username"].lower() == username.lower()), None)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000).hex()
    return f"pbkdf2:sha256:{salt}:{hashed}"


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        _, algo, salt, hashed = stored_hash.split(":", 3)
        expected = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), 260_000).hex()
        return secrets.compare_digest(expected, hashed)
    except Exception:
        return False


def create_token(user: dict) -> str:
    if not _JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured in .env")
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "display_name": user.get("display_name") or user["username"].title(),
        "role": user.get("role", "member"),
        "exp": datetime.now(timezone.utc) + timedelta(days=_TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    if not _JWT_SECRET:
        return None
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token expired")
        return None
    except Exception:
        return None


def _bot_api_key() -> str:
    return os.getenv("BOT_API_KEY", os.getenv("DASHBOARD_API_KEY", ""))


def _authenticate_request() -> tuple[Optional[dict], Optional[tuple]]:
    """Returns (user_payload, None) on success or (None, error_response_tuple) on failure."""
    bot_key = request.headers.get("X-Bot-Key", "")
    expected_bot_key = _bot_api_key()
    if bot_key and expected_bot_key and secrets.compare_digest(bot_key, expected_bot_key):
        return {"user_id": 0, "username": "bot", "display_name": "Bot", "role": "admin"}, None

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload:
            return payload, None

    return None, (jsonify({"error": "Unauthorized"}), 401)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _authenticate_request()
        if err:
            return err
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _authenticate_request()
        if err:
            return err
        g.current_user = user
        if g.current_user.get("role") != "admin":
            return jsonify({"error": "Forbidden — admin only"}), 403
        return f(*args, **kwargs)
    return decorated
