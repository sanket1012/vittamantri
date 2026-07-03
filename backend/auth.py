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


def find_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    return next((u for u in load_users() if u.get("telegram_id") == telegram_id), None)


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
        "household_id": user.get("household_id", 1),
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


def create_user(username: str, display_name: str, password: str) -> tuple[dict, str]:
    """Create a new user with their own household. Returns (user_dict, token)."""
    users = load_users()
    if any(u["username"].lower() == username.lower() for u in users):
        raise ValueError(f"Username '{username}' is already taken.")

    new_id = max((u["id"] for u in users), default=0) + 1
    new_household_id = max((u.get("household_id", 1) for u in users), default=0) + 1
    new_user = {
        "id": new_id,
        "household_id": new_household_id,
        "username": username,
        "display_name": display_name or username.title(),
        "password_hash": hash_password(password),
        "telegram_id": None,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    users.append(new_user)
    save_users(users)
    token = create_token(new_user)
    logger.info("New user registered: %s (household=%d)", username, new_household_id)
    return new_user, token


def _bot_api_key() -> str:
    return os.getenv("BOT_API_KEY", os.getenv("DASHBOARD_API_KEY", ""))


def _authenticate_request() -> tuple[Optional[dict], Optional[tuple]]:
    """Returns (user_payload, None) on success or (None, error_response_tuple) on failure."""
    bot_key = request.headers.get("X-Bot-Key", "")
    expected_bot_key = _bot_api_key()

    if bot_key and expected_bot_key and secrets.compare_digest(bot_key, expected_bot_key):
        telegram_id_str = request.headers.get("X-Telegram-Id", "")
        if telegram_id_str:
            try:
                telegram_id = int(telegram_id_str)
            except ValueError:
                return None, (jsonify({"error": "Invalid X-Telegram-Id header"}), 400)
            user = find_user_by_telegram_id(telegram_id)
            if not user:
                return None, (jsonify({"error": "not_registered"}), 403)
            payload = {
                "user_id": user["id"],
                "username": user["username"],
                "display_name": user.get("display_name") or user["username"].title(),
                "role": user.get("role", "member"),
                "household_id": user.get("household_id", 1),
            }
            return payload, None
        # Bot without Telegram ID — admin access to household 1 (legacy / health-check style)
        return {"user_id": 0, "username": "bot", "display_name": "Bot", "role": "admin", "household_id": 1}, None

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload:
            # Backfill household_id for tokens issued before multi-tenancy
            if "household_id" not in payload:
                payload["household_id"] = 1
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
