#!/usr/bin/env python3
"""Bootstrap data/users.json from DASHBOARD_USERNAME / DASHBOARD_PASSWORD env vars.

Run once on the server after upgrading to multi-user auth:
    cd ~/vittamantri/backend && python migrate_users.py

Also add these new env vars to .env:
    JWT_SECRET=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
    BOT_API_KEY=<run same command again>
"""
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000).hex()
    return f"pbkdf2:sha256:{salt}:{hashed}"


def main():
    if USERS_FILE.exists():
        try:
            existing = json.loads(USERS_FILE.read_text())
            if existing:
                print(f"users.json already has {len(existing)} user(s) — nothing to do.")
                print("Delete data/users.json first if you want to re-run migration.")
                return
        except Exception:
            pass

    username = os.getenv("DASHBOARD_USERNAME", "").strip()
    password = os.getenv("DASHBOARD_PASSWORD", "").strip()

    if not username or not password:
        print("ERROR: Set DASHBOARD_USERNAME and DASHBOARD_PASSWORD in .env first.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    users = [{
        "id": 1,
        "username": username,
        "display_name": username.title(),
        "password_hash": hash_password(password),
        "telegram_id": None,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }]
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False))
    print(f"Created {USERS_FILE} with admin user '{username}'.")
    print()
    print("Next steps:")
    print("  1. Add JWT_SECRET to .env:")
    print('     python3 -c "import secrets; print(secrets.token_hex(32))"')
    print("  2. Add BOT_API_KEY to .env (same command)")
    print("  3. Remove DASHBOARD_API_KEY, DASHBOARD_USERNAME, DASHBOARD_PASSWORD from .env")
    print("  4. pip install PyJWT")
    print("  5. sudo systemctl restart vittamantri-api vittamantri-bot")


if __name__ == "__main__":
    main()
