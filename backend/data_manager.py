"""Postgres-backed storage for VittaMantri — multi-tenant via household_id."""

from __future__ import annotations

import csv
import io
import logging
from collections import defaultdict
from datetime import date, datetime, time
from typing import Any
from uuid import uuid4

import pytz
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from categories import CATEGORIES, CATEGORY_NAMES, DEFAULT_CATEGORY, SUBCATEGORY_MAP, infer_category
from db import custom_categories, custom_subcategories, deleted_categories, engine, transactions

logger = logging.getLogger("vittamantri.data")

IST = pytz.timezone("Asia/Kolkata")

CSV_COLUMNS = [
    "id",
    "date",
    "time",
    "amount",
    "type",
    "category",
    "subcategory",
    "description",
    "source",
    "logged_by",
    "logged_by_id",
    "input_method",
    "raw_input",
]


# ── IST helpers ───────────────────────────────────────────────────────────────

def _now_ist() -> datetime:
    return datetime.now(IST)


def ensure_data_files(household_id: int) -> None:
    """No-op — a household's row is created transactionally by auth.create_user().
    Kept only because main.py calls this on login/register."""
    return None


# ── Value helpers ─────────────────────────────────────────────────────────────

def _as_float(value: Any) -> float:
    try:
        return round(float(str(value).replace(",", "").strip()), 2)
    except (TypeError, ValueError):
        return 0.0


def _short_description(value: Any) -> str:
    words = str(value or "Transaction").strip().split()
    return " ".join(words[:8]) if words else "Transaction"


_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d-%m-%y",
    "%d/%m/%y",
    "%m/%d/%Y",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %d %Y",
    "%b %d %Y",
    "%d-%b-%Y",
    "%d-%B-%Y",
    "%d %b %y",
    "%d %B %y",
    "%b %d, %y",
    "%d-%b-%y",
]


def _normalize_date(value: Any) -> date:
    if value:
        text = str(value).strip().rstrip(".,")
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                pass
        logger.warning("_normalize_date: unrecognised format %r, using today", text)
    return _now_ist().date()


def _normalize_time(value: Any) -> time:
    if value:
        text = str(value).strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                pass
    return _now_ist().time().replace(microsecond=0)


def _normalize_transaction(data: dict[str, Any]) -> dict[str, Any]:
    amount = _as_float(data.get("amount"))
    if amount <= 0:
        raise ValueError("Transaction amount must be greater than zero.")

    transaction_type = str(data.get("type") or "expense").lower().strip()
    if transaction_type not in {"income", "expense"}:
        transaction_type = "income" if "income" in transaction_type or "credit" in transaction_type else "expense"

    raw_text = " ".join(str(data.get(key) or "") for key in ("description", "source", "raw_input"))
    category = str(data.get("category") or "").strip()
    if not category:
        category = infer_category(raw_text, transaction_type) or DEFAULT_CATEGORY

    normalised_date = _normalize_date(data.get("date"))
    logger.info("_normalize_transaction: incoming date=%r → stored date=%r", data.get("date"), normalised_date)

    logged_by_id_raw = str(data.get("logged_by_id") or "0").strip() or "0"
    try:
        logged_by_id = int(logged_by_id_raw)
    except ValueError:
        logged_by_id = 0

    return {
        "id": str(data.get("id") or uuid4()),
        "date": normalised_date,
        "time": _normalize_time(data.get("time")),
        "amount": round(amount, 2),
        "type": transaction_type,
        "category": category,
        "subcategory": str(data.get("subcategory") or "").strip(),
        "description": _short_description(data.get("description")),
        "source": str(data.get("source") or "").strip(),
        "logged_by": str(data.get("logged_by") or "Unknown").strip() or "Unknown",
        "logged_by_id": logged_by_id,
        "input_method": str(data.get("input_method") or "text").lower().strip() or "text",
        "raw_input": str(data.get("raw_input") or "").strip(),
    }


def _public_row(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "date": row.date.isoformat(),
        "time": row.time.strftime("%H:%M:%S"),
        "amount": float(row.amount),
        "type": row.type,
        "category": row.category,
        "subcategory": row.subcategory,
        "description": row.description,
        "source": row.source,
        "logged_by": row.logged_by or "Unknown",
        "logged_by_id": str(row.logged_by_id or 0),
        "input_method": row.input_method,
        "raw_input": row.raw_input,
    }


def _is_garbage_row(row: dict[str, Any]) -> bool:
    return (
        _as_float(row.get("amount")) <= 0
        or not str(row.get("type") or "").strip()
        or not str(row.get("category") or "").strip()
        or not str(row.get("date") or "").strip()
    )


def _summary_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_income = 0.0
    total_expense = 0.0
    for row in rows:
        amount = _as_float(row.get("amount"))
        if str(row.get("type") or "").lower() == "income":
            total_income += amount
        else:
            total_expense += amount
    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(total_income - total_expense, 2),
        "transaction_count": len(rows),
    }


# ── Public read functions ─────────────────────────────────────────────────────

def get_all_transactions(household_id: int) -> list[dict[str, Any]]:
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                select(transactions)
                .where(transactions.c.household_id == household_id)
                .order_by(transactions.c.date.desc(), transactions.c.time.desc())
            ).all()
        return [_public_row(r) for r in rows]
    except Exception as exc:
        raise RuntimeError(f"Unable to read transactions: {exc}") from exc


def get_transactions_by_month(year: int, month: int, household_id: int) -> list[dict[str, Any]]:
    prefix = f"{year:04d}-{month:02d}"
    return [r for r in get_all_transactions(household_id) if str(r.get("date", "")).startswith(prefix)]


def get_transactions_by_category(category: str, household_id: int) -> list[dict[str, Any]]:
    return [r for r in get_all_transactions(household_id) if r.get("category") == category]


def get_transactions_by_user(logged_by_id: int, household_id: int) -> list[dict[str, Any]]:
    user_id = str(logged_by_id)
    return [r for r in get_all_transactions(household_id) if str(r.get("logged_by_id") or "0") == user_id]


def get_all_users(household_id: int) -> list[dict[str, Any]]:
    users: dict[str, dict[str, Any]] = {}
    for row in get_all_transactions(household_id):
        user_id = str(row.get("logged_by_id") or "0")
        name = row.get("logged_by") or "Unknown"
        users.setdefault(user_id, {"logged_by": name, "logged_by_id": int(user_id) if user_id.isdigit() else 0, "count": 0})
        users[user_id]["logged_by"] = name
        users[user_id]["count"] += 1
    return sorted(users.values(), key=lambda item: item["logged_by"].lower())


def get_user_summary(logged_by_id: int, household_id: int) -> dict[str, Any]:
    return _summary_from_rows(get_transactions_by_user(logged_by_id, household_id))


def _deleted_category_names(household_id: int) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            select(deleted_categories.c.name).where(deleted_categories.c.household_id == household_id)
        ).all()
    return {r.name for r in rows}


def get_categories(household_id: int) -> list[dict[str, str]]:
    deleted = _deleted_category_names(household_id)
    names: set[str] = {n for n in CATEGORY_NAMES if n not in deleted}
    for row in get_all_transactions(household_id):
        category = str(row.get("category") or "").strip()
        if category and category not in deleted:
            names.add(category)
    return [
        {"name": name, "emoji": CATEGORIES.get(name, {}).get("emoji", "🏷️")}
        for name in sorted(names)
    ]


def compute_summary(household_id: int) -> dict[str, Any]:
    with engine.connect() as conn:
        type_totals = dict(conn.execute(
            select(transactions.c.type, func.sum(transactions.c.amount))
            .where(transactions.c.household_id == household_id)
            .group_by(transactions.c.type)
        ).all())
        expense_by_category = dict(conn.execute(
            select(transactions.c.category, func.sum(transactions.c.amount))
            .where(transactions.c.household_id == household_id, transactions.c.type == "expense")
            .group_by(transactions.c.category)
        ).all())
        seen_categories = conn.execute(
            select(transactions.c.category.distinct()).where(transactions.c.household_id == household_id)
        ).scalars().all()
        monthly_rows = conn.execute(
            select(
                func.to_char(transactions.c.date, "YYYY-MM").label("month"),
                transactions.c.type,
                func.sum(transactions.c.amount),
            )
            .where(transactions.c.household_id == household_id)
            .group_by("month", transactions.c.type)
            .order_by("month")
        ).all()
        transaction_count = conn.execute(
            select(func.count(transactions.c.id)).where(transactions.c.household_id == household_id)
        ).scalar_one()

    total_income = float(type_totals.get("income") or 0)
    total_expense = float(type_totals.get("expense") or 0)

    category_totals: dict[str, float] = {name: 0.0 for name in CATEGORY_NAMES}
    for name in seen_categories:
        category_totals.setdefault(name, 0.0)
    for name, total in expense_by_category.items():
        category_totals[name] = float(total)
    category_totals = {k: round(v, 2) for k, v in sorted(category_totals.items())}

    monthly_totals: dict[str, dict[str, float]] = {}
    for month, txn_type, total in monthly_rows:
        monthly_totals.setdefault(month, {"income": 0.0, "expense": 0.0})
        monthly_totals[month][txn_type] = round(float(total), 2)
    monthly_totals = dict(sorted(monthly_totals.items()))

    return {
        "last_updated": _now_ist().replace(microsecond=0).isoformat(),
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(total_income - total_expense, 2),
        "transaction_count": transaction_count,
        "category_totals": category_totals,
        "monthly_totals": monthly_totals,
    }


def get_summary(household_id: int) -> dict[str, Any]:
    return compute_summary(household_id)


def rebuild_summary(household_id: int) -> dict[str, Any]:
    return compute_summary(household_id)


# ── Public write functions ────────────────────────────────────────────────────

def save_transaction(data: dict[str, Any], household_id: int) -> str:
    try:
        row = _normalize_transaction(data)
        with engine.begin() as conn:
            conn.execute(insert(transactions).values(household_id=household_id, **row))
        return row["id"]
    except Exception as exc:
        raise RuntimeError(f"Unable to save transaction: {exc}") from exc


def update_transaction_category(id: str, category: str, household_id: int) -> bool:
    return update_transaction_fields(id, {"category": category}, household_id)


_MUTABLE_FIELDS = {"category", "subcategory", "description", "source", "type", "amount", "date"}


def _normalize_field(key: str, value: Any) -> Any:
    if key == "amount":
        amount = _as_float(value)
        return round(amount, 2) if amount > 0 else None
    if key == "date":
        return _normalize_date(value)
    if key == "type":
        val = str(value).lower().strip()
        return val if val in {"income", "expense"} else None
    return str(value).strip()


def update_transaction_fields(id: str, fields: dict[str, Any], household_id: int) -> bool:
    normalized = {k: _normalize_field(k, v) for k, v in fields.items() if k in _MUTABLE_FIELDS}
    normalized = {k: v for k, v in normalized.items() if v is not None}
    if not normalized:
        return False
    try:
        with engine.begin() as conn:
            result = conn.execute(
                update(transactions)
                .where(transactions.c.id == id, transactions.c.household_id == household_id)
                .values(**normalized)
            )
            return result.rowcount > 0
    except Exception as exc:
        raise RuntimeError(f"Unable to update transaction: {exc}") from exc


def bulk_update_transactions(ids: list[str], fields: dict[str, Any], household_id: int) -> int:
    normalized = {k: _normalize_field(k, v) for k, v in fields.items() if k in _MUTABLE_FIELDS}
    normalized = {k: v for k, v in normalized.items() if v is not None}
    if not normalized or not ids:
        return 0
    try:
        with engine.begin() as conn:
            result = conn.execute(
                update(transactions)
                .where(transactions.c.id.in_(ids), transactions.c.household_id == household_id)
                .values(**normalized)
            )
            return result.rowcount
    except Exception as exc:
        raise RuntimeError(f"Unable to bulk update transactions: {exc}") from exc


def delete_transaction(id: str, household_id: int) -> bool:
    try:
        with engine.begin() as conn:
            result = conn.execute(
                delete(transactions).where(transactions.c.id == id, transactions.c.household_id == household_id)
            )
            return result.rowcount > 0
    except Exception as exc:
        raise RuntimeError(f"Unable to delete transaction: {exc}") from exc


def clean_garbage(household_id: int) -> int:
    """Historically dropped rows with a non-positive amount. The `amount > 0`
    CHECK constraint means Postgres never accepts such a row in the first place,
    so this now always affects 0 rows — kept only so the existing
    "clean garbage" endpoint/button keeps working."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                delete(transactions).where(
                    transactions.c.household_id == household_id, transactions.c.amount <= 0
                )
            )
            return result.rowcount
    except Exception as exc:
        raise RuntimeError(f"Unable to clean garbage transactions: {exc}") from exc


def export_monthly_report(year: int, month: int, household_id: int) -> str:
    try:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in get_transactions_by_month(year, month, household_id):
            writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})
        return output.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Unable to export monthly report: {exc}") from exc


def export_all_csv(household_id: int) -> str:
    try:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in get_all_transactions(household_id):
            writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})
        return output.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Unable to export transactions: {exc}") from exc


# ── Custom categories ─────────────────────────────────────────────────────────

def get_categories_with_subcategories(household_id: int) -> list[dict[str, Any]]:
    deleted = _deleted_category_names(household_id)
    with engine.connect() as conn:
        custom_cat_rows = conn.execute(
            select(custom_categories.c.name, custom_categories.c.emoji)
            .where(custom_categories.c.household_id == household_id)
            .order_by(custom_categories.c.name)
        ).all()
        custom_sub_rows = conn.execute(
            select(custom_subcategories.c.category_name, custom_subcategories.c.name)
            .where(custom_subcategories.c.household_id == household_id)
            .order_by(custom_subcategories.c.category_name, custom_subcategories.c.name)
        ).all()

    custom_subs_by_category: dict[str, list[str]] = defaultdict(list)
    for r in custom_sub_rows:
        custom_subs_by_category[r.category_name].append(r.name)

    result: list[dict[str, Any]] = []
    known: set[str] = set()

    for name in CATEGORY_NAMES:
        if name in deleted:
            known.add(name)
            continue
        meta = CATEGORIES.get(name, {})
        builtin_subs = list(SUBCATEGORY_MAP.get(name, []))
        custom_subs = [s for s in custom_subs_by_category.get(name, []) if s not in builtin_subs]
        result.append({
            "name": name,
            "emoji": meta.get("emoji", "🏷️"),
            "subcategories": builtin_subs + custom_subs,
            "custom_subcategories": custom_subs,
            "is_custom": False,
        })
        known.add(name)

    for row in custom_cat_rows:
        name = row.name
        if name in known:
            continue
        custom_subs = list(custom_subs_by_category.get(name, []))
        result.append({
            "name": name,
            "emoji": row.emoji,
            "subcategories": custom_subs,
            "custom_subcategories": custom_subs,
            "is_custom": True,
        })
        known.add(name)

    for row in get_all_transactions(household_id):
        cat = str(row.get("category") or "").strip()
        if cat and cat not in known:
            custom_subs = list(custom_subs_by_category.get(cat, []))
            result.append({
                "name": cat,
                "emoji": "🏷️",
                "subcategories": custom_subs,
                "custom_subcategories": custom_subs,
                "is_custom": True,
            })
            known.add(cat)

    return result


def save_custom_category(name: str, emoji: str = "🏷️", *, household_id: int) -> None:
    stmt = pg_insert(custom_categories).values(household_id=household_id, name=name, emoji=emoji)
    stmt = stmt.on_conflict_do_nothing(index_elements=["household_id", "name"])
    with engine.begin() as conn:
        conn.execute(stmt)


def save_custom_subcategory(category_name: str, subcategory: str, *, household_id: int) -> None:
    stmt = pg_insert(custom_subcategories).values(household_id=household_id, category_name=category_name, name=subcategory)
    stmt = stmt.on_conflict_do_nothing(index_elements=["household_id", "category_name", "name"])
    with engine.begin() as conn:
        conn.execute(stmt)


def delete_category(name: str, household_id: int) -> bool:
    if not name:
        return False
    with engine.begin() as conn:
        if name in CATEGORY_NAMES:
            stmt = pg_insert(deleted_categories).values(household_id=household_id, name=name)
            stmt = stmt.on_conflict_do_nothing(index_elements=["household_id", "name"])
            conn.execute(stmt)
        else:
            conn.execute(
                delete(custom_categories).where(
                    custom_categories.c.household_id == household_id, custom_categories.c.name == name
                )
            )
        conn.execute(
            delete(custom_subcategories).where(
                custom_subcategories.c.household_id == household_id,
                custom_subcategories.c.category_name == name,
            )
        )
    return True


delete_custom_category = delete_category


def delete_custom_subcategory(category_name: str, subcategory: str, household_id: int) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            delete(custom_subcategories).where(
                custom_subcategories.c.household_id == household_id,
                custom_subcategories.c.category_name == category_name,
                custom_subcategories.c.name == subcategory,
            )
        )
        return result.rowcount > 0
