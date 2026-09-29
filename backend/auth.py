import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional

import jwt
from flask import g, jsonify, request
from sqlalchemy import delete, insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from db import engine, households, member_invites, users as users_table

logger = logging.getLogger("vittamantri.auth")

_JWT_SECRET = os.getenv("JWT_SECRET", "")
_TOKEN_EXPIRY_DAYS = 30


def _row_to_dict(row) -> dict:
    return {
        "id": row.id,
        "household_id": row.household_id,
        "username": row.username,
        "display_name": row.display_name,
        "password_hash": row.password_hash,
        "telegram_id": row.telegram_id,
        "role": row.role,
        "created_at": row.created_at.strftime("%Y-%m-%d") if row.created_at else None,
    }


def load_users() -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(select(users_table)).all()
    return [_row_to_dict(r) for r in rows]


def save_users(users: list[dict]) -> None:
    """Reconciles the DB against a full user list, mirroring the old
    "load whole file, mutate in Python, save whole file back" pattern that
    main.py's member-management routes rely on: any id missing from `users`
    is deleted, everything else is upserted."""
    ids = [u["id"] for u in users]
    with engine.begin() as conn:
        if ids:
            conn.execute(delete(users_table).where(users_table.c.id.notin_(ids)))
        else:
            conn.execute(delete(users_table))
        for u in users:
            values = {
                "household_id": u.get("household_id", 1),
                "username": u["username"],
                "display_name": u.get("display_name") or u["username"].title(),
                "password_hash": u["password_hash"],
                "telegram_id": u.get("telegram_id"),
                "role": u.get("role", "member"),
            }
            stmt = pg_insert(users_table).values(id=u["id"], **values)
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=values)
            conn.execute(stmt)
        # Explicit-id inserts (e.g. main.py's add_member, which computes its own
        # next id) don't advance `users.id`'s identity sequence, so a later
        # auto-generated insert (create_user's registration flow) could try to
        # reuse an id that's still in use. Re-sync after every write.
        conn.execute(
            text("SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT COALESCE(MAX(id), 0) FROM users), true)")
        )


def get_user_by_id(user_id: int) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(select(users_table).where(users_table.c.id == user_id)).first()
    return _row_to_dict(row) if row else None


def get_user_by_username(username: str) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(select(users_table).where(users_table.c.username == username)).first()
    return _row_to_dict(row) if row else None


def find_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(select(users_table).where(users_table.c.telegram_id == telegram_id)).first()
    return _row_to_dict(row) if row else None


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
    try:
        with engine.begin() as conn:
            household_id = conn.execute(insert(households).returning(households.c.id)).scalar_one()
            new_id = conn.execute(
                insert(users_table)
                .values(
                    household_id=household_id,
                    username=username,
                    display_name=display_name or username.title(),
                    password_hash=hash_password(password),
                    telegram_id=None,
                    role="admin",
                )
                .returning(users_table.c.id)
            ).scalar_one()
    except IntegrityError as exc:
        raise ValueError(f"Username '{username}' is already taken.") from exc

    new_user = get_user_by_id(new_id)
    token = create_token(new_user)
    logger.info("New user registered: %s (household=%d)", username, new_user["household_id"])
    return new_user, token


_INVITE_TTL_DAYS = 7


def create_member_invite(household_id: int, phone_number: str, display_name: str, created_by: int) -> dict:
    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(days=_INVITE_TTL_DAYS)
    with engine.begin() as conn:
        new_id = conn.execute(
            insert(member_invites)
            .values(
                household_id=household_id,
                phone_number=phone_number,
                display_name=display_name,
                token=token,
                status="pending",
                created_by=created_by,
                expires_at=expires_at,
            )
            .returning(member_invites.c.id)
        ).scalar_one()
    return {"id": new_id, "token": token, "expires_at": expires_at}


def list_pending_invites(household_id: int) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            select(member_invites)
            .where(member_invites.c.household_id == household_id, member_invites.c.status == "pending")
            .order_by(member_invites.c.created_at.desc())
        ).all()
    return [
        {
            "id": r.id,
            "phone_number": r.phone_number,
            "display_name": r.display_name,
            "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else None,
            "expires_at": r.expires_at.strftime("%Y-%m-%d") if r.expires_at else None,
        }
        for r in rows
    ]


def cancel_member_invite(invite_id: int, household_id: int) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            member_invites.update()
            .where(member_invites.c.id == invite_id, member_invites.c.household_id == household_id, member_invites.c.status == "pending")
            .values(status="cancelled")
        )
    return result.rowcount > 0


def get_invite_preview(token: str) -> Optional[dict]:
    """Public-facing preview for the accept-invite page. None if invalid/expired/consumed."""
    with engine.connect() as conn:
        row = conn.execute(select(member_invites).where(member_invites.c.token == token)).first()
        if not row or row.status != "pending" or row.expires_at < datetime.now(timezone.utc):
            return None
        inviter = conn.execute(select(users_table.c.display_name).where(users_table.c.id == row.created_by)).first()
    return {
        "display_name": row.display_name,
        "inviter_name": inviter.display_name if inviter else "your household",
    }


def accept_member_invite(token: str, username: str, display_name: str, password: str) -> tuple[dict, str]:
    """Validates an invite and creates the joining user atomically — if user
    creation fails (e.g. duplicate username), the invite stays pending rather
    than being burned with no user attached. Returns (user_dict, jwt_token).
    Raises ValueError for an invalid/expired invite or a taken username."""
    with engine.begin() as conn:
        row = conn.execute(select(member_invites).where(member_invites.c.token == token)).first()
        if not row or row.status != "pending" or row.expires_at < datetime.now(timezone.utc):
            raise ValueError("This invite link is invalid or has expired.")

        try:
            new_id = conn.execute(
                insert(users_table)
                .values(
                    household_id=row.household_id,
                    username=username,
                    display_name=display_name or username.title(),
                    password_hash=hash_password(password),
                    telegram_id=None,
                    role="member",
                )
                .returning(users_table.c.id)
            ).scalar_one()
        except IntegrityError as exc:
            raise ValueError(f"Username '{username}' is already taken.") from exc

        conn.execute(
            member_invites.update().where(member_invites.c.id == row.id).values(status="accepted", accepted_user_id=new_id)
        )

    new_user = get_user_by_id(new_id)
    token_jwt = create_token(new_user)
    logger.info("New user %s joined household=%d via invite", username, row.household_id)
    return new_user, token_jwt


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


_TELEGRAM_LOGIN_MAX_AGE_SECONDS = 300


def verify_telegram_login(data: dict) -> bool:
    """Verifies a Telegram Login Widget payload's authenticity and freshness.
    See https://core.telegram.org/widgets/login#checking-authorization"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    received_hash = data.get("hash")
    if not bot_token or not received_hash:
        return False

    check_fields = {k: v for k, v in data.items() if k != "hash"}
    data_check_string = "\n".join(f"{k}={check_fields[k]}" for k in sorted(check_fields))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, str(received_hash)):
        return False

    try:
        auth_date = int(data.get("auth_date", 0))
    except (TypeError, ValueError):
        return False
    age = datetime.now(timezone.utc).timestamp() - auth_date
    return 0 <= age <= _TELEGRAM_LOGIN_MAX_AGE_SECONDS


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
