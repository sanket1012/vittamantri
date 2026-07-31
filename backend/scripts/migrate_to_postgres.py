#!/usr/bin/env python3
"""One-off migration: copies existing data/h_*/transactions.csv + data/users.json
into the Supabase Postgres tables created by the Alembic initial revision.

Usage (run from backend/):
    python scripts/migrate_to_postgres.py            # dry run (default) — prints counts only
    python scripts/migrate_to_postgres.py --apply    # writes to Postgres, then verifies

Never deletes or modifies data/h_*/ or data/users.json — they remain the
rollback path. Safe to re-run: transactions upsert on their existing UUID `id`,
users upsert on their existing integer `id`, and households upsert on `id`
(ON CONFLICT DO NOTHING/UPDATE throughout).

This script intentionally does NOT import auth.py/data_manager.py's
load_users()/get_all_transactions() — those now talk to Postgres, not the
legacy files, so this script reads the legacy CSV/JSON directly instead.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select, text  # noqa: E402
from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402

from data_manager import _as_float, _is_garbage_row  # noqa: E402
from db import engine, households, transactions  # noqa: E402
from db import users as users_table  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"


# ── Legacy file readers ───────────────────────────────────────────────────────

def load_legacy_users() -> list[dict[str, Any]]:
    if not USERS_FILE.exists():
        return []
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def load_legacy_transactions(household_id: int) -> list[dict[str, Any]]:
    csv_path = DATA_DIR / f"h_{household_id}" / "transactions.csv"
    if not csv_path.exists():
        return []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def household_ids_from_legacy_users(legacy_users: list[dict[str, Any]]) -> list[int]:
    if legacy_users:
        return sorted({int(u.get("household_id", 1)) for u in legacy_users})
    return [1] if (DATA_DIR / "h_1").exists() else []


# ── CSV row → Postgres row conversion ─────────────────────────────────────────

def _parse_date(value: str):
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def _parse_time(value: str):
    value = (value or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            pass
    return datetime.strptime("00:00:00", "%H:%M:%S").time()


def _row_to_insert_values(row: dict[str, Any], household_id: int) -> dict[str, Any]:
    logged_by_id_raw = str(row.get("logged_by_id") or "0").strip() or "0"
    try:
        logged_by_id = int(logged_by_id_raw)
    except ValueError:
        logged_by_id = 0
    return {
        "id": row["id"],
        "household_id": household_id,
        "date": _parse_date(row["date"]),
        "time": _parse_time(row.get("time")),
        "amount": _as_float(row.get("amount")),
        "type": (row.get("type") or "expense").strip().lower(),
        "category": (row.get("category") or "").strip(),
        "subcategory": (row.get("subcategory") or "").strip(),
        "description": (row.get("description") or "").strip(),
        "source": (row.get("source") or "").strip(),
        "logged_by": (row.get("logged_by") or "Unknown").strip() or "Unknown",
        "logged_by_id": logged_by_id,
        "input_method": (row.get("input_method") or "text").strip().lower() or "text",
        "raw_input": (row.get("raw_input") or "").strip(),
    }


# ── Write phase (FK order: households → users → transactions) ────────────────

def _bump_identity_sequence(conn, table: str, max_id: int) -> None:
    """Advance the table's identity sequence past `max_id` so the next
    app-generated insert (e.g. a new registration) doesn't collide with an id
    this script just wrote explicitly."""
    if max_id <= 0:
        return
    conn.execute(
        text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), :max_id, true)"),
        {"max_id": max_id},
    )


def write_households(conn, household_ids: list[int]) -> None:
    for hid in household_ids:
        stmt = pg_insert(households).values(id=hid).on_conflict_do_nothing(index_elements=["id"])
        conn.execute(stmt)
    if household_ids:
        _bump_identity_sequence(conn, "households", max(household_ids))


def write_users(conn, legacy_users: list[dict[str, Any]]) -> None:
    for u in legacy_users:
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
    if legacy_users:
        _bump_identity_sequence(conn, "users", max(u["id"] for u in legacy_users))


def write_transactions(conn, household_id: int, rows: list[dict[str, Any]]) -> int:
    for row in rows:
        values = _row_to_insert_values(row, household_id)
        stmt = pg_insert(transactions).values(**values)
        update_cols = {k: v for k, v in values.items() if k != "id"}
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
        conn.execute(stmt)
    return len(rows)


# ── Post-apply verification ───────────────────────────────────────────────────

def verify(household_ids: list[int]) -> bool:
    all_ok = True
    with engine.connect() as conn:
        for hid in household_ids:
            legacy_rows = [r for r in load_legacy_transactions(hid) if not _is_garbage_row(r)]
            expected_count = len(legacy_rows)
            expected_sums: dict[str, float] = defaultdict(float)
            for r in legacy_rows:
                expected_sums[(r.get("type") or "expense").strip().lower()] += _as_float(r.get("amount"))

            actual_count = conn.execute(
                select(func.count(transactions.c.id)).where(transactions.c.household_id == hid)
            ).scalar_one()
            actual_sums = dict(
                conn.execute(
                    select(transactions.c.type, func.sum(transactions.c.amount))
                    .where(transactions.c.household_id == hid)
                    .group_by(transactions.c.type)
                ).all()
            )

            household_ok = actual_count == expected_count
            if not household_ok:
                print(f"  MISMATCH household {hid}: row count expected={expected_count} actual={actual_count}")

            for txn_type, expected_total in expected_sums.items():
                actual_total = float(actual_sums.get(txn_type) or 0)
                if round(actual_total, 2) != round(expected_total, 2):
                    print(
                        f"  MISMATCH household {hid} [{txn_type}]: "
                        f"expected sum={expected_total:.2f} actual sum={actual_total:.2f}"
                    )
                    household_ok = False

            if household_ok:
                print(f"  OK household {hid}: {actual_count} transaction(s), sums match")
            all_ok = all_ok and household_ok
    return all_ok


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    global DATA_DIR, USERS_FILE

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write to Postgres (default is dry-run).")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Override the data/ directory to read from (defaults to <repo_root>/data). "
        "Use this to validate against a copied-down production data/ folder without "
        "touching this repo's own data/.",
    )
    args = parser.parse_args()

    if args.data_dir:
        DATA_DIR = args.data_dir.resolve()
        USERS_FILE = DATA_DIR / "users.json"

    print(f"Reading legacy data from: {DATA_DIR}")
    legacy_users = load_legacy_users()
    household_ids = household_ids_from_legacy_users(legacy_users)
    print(f"Found {len(legacy_users)} user(s) across {len(household_ids)} household(s): {household_ids}")

    per_household_rows: dict[int, list[dict[str, Any]]] = {}
    total_clean, total_garbage = 0, 0
    for hid in household_ids:
        rows = load_legacy_transactions(hid)
        clean_rows = [r for r in rows if not _is_garbage_row(r)]
        garbage = len(rows) - len(clean_rows)
        per_household_rows[hid] = clean_rows
        total_clean += len(clean_rows)
        total_garbage += garbage
        print(f"  household {hid}: {len(clean_rows)} transaction(s) to migrate, {garbage} garbage row(s) skipped")

    print(
        f"\nTotal: {total_clean} transaction(s) to migrate ({total_garbage} garbage skipped), "
        f"{len(legacy_users)} user(s), {len(household_ids)} household(s)."
    )

    if not args.apply:
        print("\nDry run only — no changes made. Re-run with --apply to write to Postgres.")
        return

    print("\nApplying migration...")
    with engine.begin() as conn:
        write_households(conn, household_ids)
        write_users(conn, legacy_users)
        for hid in household_ids:
            count = write_transactions(conn, hid, per_household_rows[hid])
            print(f"  household {hid}: wrote {count} transaction(s)")

    print("\nVerifying...")
    if not verify(household_ids):
        print("\nVERIFICATION FAILED — Postgres data does not match source files. Investigate before cutover.")
        sys.exit(1)
    print("\nVerification passed. Postgres data matches source files.")


if __name__ == "__main__":
    main()
