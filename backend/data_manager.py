"""CSV and JSON storage for VittaMantri — multi-tenant, one directory per household."""

from __future__ import annotations

import csv
import io
import json
import logging
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytz

from categories import CATEGORIES, CATEGORY_NAMES, DEFAULT_CATEGORY, SUBCATEGORY_MAP, infer_category

logger = logging.getLogger("vittamantri.data")

IST = pytz.timezone("Asia/Kolkata")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

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

# Per-household locks: prevents concurrent writes to the same household's files.
_locks: dict[int, threading.Lock] = defaultdict(threading.Lock)


def _lock_for(household_id: int) -> threading.Lock:
    return _locks[household_id]


def _get_paths(household_id: int) -> dict[str, Path]:
    base = DATA_DIR / f"h_{household_id}"
    return {
        "dir": base,
        "transactions": base / "transactions.csv",
        "summary": base / "summary.json",
        "categories_extra": base / "categories_extra.json",
    }


# ── IST helpers ───────────────────────────────────────────────────────────────

def _now_ist() -> datetime:
    return datetime.now(IST)


def _empty_summary() -> dict[str, Any]:
    return {
        "last_updated": _now_ist().replace(microsecond=0).isoformat(),
        "total_income": 0.0,
        "total_expense": 0.0,
        "net_savings": 0.0,
        "transaction_count": 0,
        "category_totals": {category: 0.0 for category in CATEGORY_NAMES},
        "monthly_totals": {},
    }


# ── File I/O helpers (all take explicit paths) ────────────────────────────────

def ensure_data_files(household_id: int) -> None:
    paths = _get_paths(household_id)
    try:
        paths["dir"].mkdir(parents=True, exist_ok=True)
        if not paths["transactions"].exists():
            with paths["transactions"].open("w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()
        else:
            _migrate_transactions_file(paths["transactions"])
        if not paths["summary"].exists():
            _write_summary_to(paths["summary"], _empty_summary())
    except OSError as exc:
        raise RuntimeError(f"Unable to initialize data files for household {household_id}: {exc}") from exc


def _migrate_transactions_file(transactions_file: Path) -> None:
    with transactions_file.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames == CSV_COLUMNS:
            return
        rows = list(reader)
    with transactions_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})


def _write_summary_to(summary_file: Path, summary: dict[str, Any]) -> None:
    with summary_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def _read_rows_unlocked(household_id: int) -> list[dict[str, str]]:
    ensure_data_files(household_id)
    transactions_file = _get_paths(household_id)["transactions"]
    with transactions_file.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_rows_unlocked(household_id: int, rows: list[dict[str, Any]]) -> None:
    ensure_data_files(household_id)
    transactions_file = _get_paths(household_id)["transactions"]
    with transactions_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows([{col: row.get(col, "") for col in CSV_COLUMNS} for row in rows])


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


def _normalize_date(value: Any) -> str:
    if value:
        text = str(value).strip().rstrip(".,")
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        logger.warning("_normalize_date: unrecognised format %r, using today", text)
    return _now_ist().strftime("%Y-%m-%d")


def _normalize_time(value: Any) -> str:
    if value:
        text = str(value).strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(text, fmt).strftime("%H:%M:%S")
            except ValueError:
                pass
    return _now_ist().strftime("%H:%M:%S")


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
    return {
        "id": str(data.get("id") or uuid4()),
        "date": normalised_date,
        "time": _normalize_time(data.get("time")),
        "amount": f"{amount:.2f}",
        "type": transaction_type,
        "category": category,
        "subcategory": str(data.get("subcategory") or "").strip(),
        "description": _short_description(data.get("description")),
        "source": str(data.get("source") or "").strip(),
        "logged_by": str(data.get("logged_by") or "Unknown").strip() or "Unknown",
        "logged_by_id": str(data.get("logged_by_id") or "0").strip() or "0",
        "input_method": str(data.get("input_method") or "text").lower().strip() or "text",
        "raw_input": str(data.get("raw_input") or "").strip(),
    }


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    item = {col: row.get(col, "") for col in CSV_COLUMNS}
    item["logged_by"] = item.get("logged_by") or "Unknown"
    item["logged_by_id"] = str(item.get("logged_by_id") or "0")
    item["amount"] = _as_float(item["amount"])
    return item


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


def _recalculate_summary_unlocked(household_id: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _empty_summary()
    for row in rows:
        amount = _as_float(row.get("amount"))
        transaction_type = str(row.get("type") or "expense").lower()
        category = str(row.get("category") or DEFAULT_CATEGORY).strip() or DEFAULT_CATEGORY
        month_key = str(row.get("date") or "")[:7] or _now_ist().strftime("%Y-%m")

        summary["category_totals"].setdefault(category, 0.0)
        if transaction_type == "income":
            summary["total_income"] += amount
        else:
            summary["total_expense"] += amount
            summary["category_totals"][category] += amount

        summary["monthly_totals"].setdefault(month_key, {"income": 0.0, "expense": 0.0})
        summary["monthly_totals"][month_key].setdefault(transaction_type, 0.0)
        summary["monthly_totals"][month_key][transaction_type] += amount

    summary["total_income"] = round(summary["total_income"], 2)
    summary["total_expense"] = round(summary["total_expense"], 2)
    summary["net_savings"] = round(summary["total_income"] - summary["total_expense"], 2)
    summary["transaction_count"] = len(rows)
    summary["category_totals"] = {k: round(v, 2) for k, v in sorted(summary["category_totals"].items())}
    summary["monthly_totals"] = {
        k: {"income": round(v.get("income", 0.0), 2), "expense": round(v.get("expense", 0.0), 2)}
        for k, v in sorted(summary["monthly_totals"].items())
    }
    summary["last_updated"] = _now_ist().replace(microsecond=0).isoformat()
    _write_summary_to(_get_paths(household_id)["summary"], summary)
    return summary


# ── Public read functions ─────────────────────────────────────────────────────

def get_all_transactions(household_id: int) -> list[dict[str, Any]]:
    try:
        rows = _read_rows_unlocked(household_id)
        return sorted((_public_row(r) for r in rows), key=lambda r: (r["date"], r["time"]), reverse=True)
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


def get_categories(household_id: int) -> list[dict[str, str]]:
    deleted: set[str] = set(_read_extra_categories(household_id).get("deleted_categories", []))
    names: set[str] = {n for n in CATEGORY_NAMES if n not in deleted}
    for row in get_all_transactions(household_id):
        category = str(row.get("category") or "").strip()
        if category and category not in deleted:
            names.add(category)
    return [
        {"name": name, "emoji": CATEGORIES.get(name, {}).get("emoji", "🏷️")}
        for name in sorted(names)
    ]


def get_summary(household_id: int) -> dict[str, Any]:
    paths = _get_paths(household_id)
    ensure_data_files(household_id)
    try:
        with paths["summary"].open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        with _lock_for(household_id):
            return _recalculate_summary_unlocked(household_id, _read_rows_unlocked(household_id))


# ── Public write functions ────────────────────────────────────────────────────

def save_transaction(data: dict[str, Any], household_id: int) -> str:
    try:
        row = _normalize_transaction(data)
        with _lock_for(household_id):
            rows = _read_rows_unlocked(household_id)
            rows.append(row)
            _write_rows_unlocked(household_id, rows)
            _recalculate_summary_unlocked(household_id, rows)
        return row["id"]
    except Exception as exc:
        raise RuntimeError(f"Unable to save transaction: {exc}") from exc


def rebuild_summary(household_id: int) -> dict[str, Any]:
    with _lock_for(household_id):
        return _recalculate_summary_unlocked(household_id, _read_rows_unlocked(household_id))


def update_transaction_category(id: str, category: str, household_id: int) -> bool:
    return update_transaction_fields(id, {"category": category}, household_id)


_MUTABLE_FIELDS = {"category", "subcategory", "description", "source", "type", "amount", "date"}


def _normalize_field(key: str, value: Any) -> str | None:
    if key == "amount":
        amount = _as_float(value)
        return f"{amount:.2f}" if amount > 0 else None
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
        with _lock_for(household_id):
            rows = _read_rows_unlocked(household_id)
            for row in rows:
                if row.get("id") == id:
                    row.update(normalized)
                    _write_rows_unlocked(household_id, rows)
                    _recalculate_summary_unlocked(household_id, rows)
                    return True
            return False
    except Exception as exc:
        raise RuntimeError(f"Unable to update transaction: {exc}") from exc


def bulk_update_transactions(ids: list[str], fields: dict[str, Any], household_id: int) -> int:
    normalized = {k: _normalize_field(k, v) for k, v in fields.items() if k in _MUTABLE_FIELDS}
    normalized = {k: v for k, v in normalized.items() if v is not None}
    if not normalized or not ids:
        return 0
    id_set = set(ids)
    try:
        with _lock_for(household_id):
            rows = _read_rows_unlocked(household_id)
            count = sum(1 for row in rows if row.get("id") in id_set)
            if not count:
                return 0
            for row in rows:
                if row.get("id") in id_set:
                    row.update(normalized)
            _write_rows_unlocked(household_id, rows)
            _recalculate_summary_unlocked(household_id, rows)
            return count
    except Exception as exc:
        raise RuntimeError(f"Unable to bulk update transactions: {exc}") from exc


def delete_transaction(id: str, household_id: int) -> bool:
    try:
        with _lock_for(household_id):
            rows = _read_rows_unlocked(household_id)
            remaining = [r for r in rows if r.get("id") != id]
            if len(remaining) == len(rows):
                return False
            _write_rows_unlocked(household_id, remaining)
            _recalculate_summary_unlocked(household_id, remaining)
            return True
    except Exception as exc:
        raise RuntimeError(f"Unable to delete transaction: {exc}") from exc


def clean_garbage(household_id: int) -> int:
    try:
        with _lock_for(household_id):
            rows = _read_rows_unlocked(household_id)
            clean_rows = [r for r in rows if not _is_garbage_row(r)]
            deleted_count = len(rows) - len(clean_rows)
            if deleted_count:
                _write_rows_unlocked(household_id, clean_rows)
            _recalculate_summary_unlocked(household_id, clean_rows)
            return deleted_count
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


def transaction_csv_path(household_id: int) -> Path:
    ensure_data_files(household_id)
    return _get_paths(household_id)["transactions"]


# ── Custom categories ─────────────────────────────────────────────────────────

def _read_extra_categories(household_id: int) -> dict[str, Any]:
    cats_file = _get_paths(household_id)["categories_extra"]
    if not cats_file.exists():
        return {"categories": [], "subcategories": {}}
    try:
        with cats_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"categories": [], "subcategories": {}}


def _write_extra_categories(household_id: int, data: dict[str, Any]) -> None:
    paths = _get_paths(household_id)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    with paths["categories_extra"].open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_categories_with_subcategories(household_id: int) -> list[dict[str, Any]]:
    extra = _read_extra_categories(household_id)
    deleted: set[str] = set(extra.get("deleted_categories", []))
    result: list[dict[str, Any]] = []
    known: set[str] = set()

    for name in CATEGORY_NAMES:
        if name in deleted:
            known.add(name)
            continue
        meta = CATEGORIES.get(name, {})
        builtin_subs = list(SUBCATEGORY_MAP.get(name, []))
        custom_subs = [s for s in extra.get("subcategories", {}).get(name, []) if s not in builtin_subs]
        result.append({
            "name": name,
            "emoji": meta.get("emoji", "🏷️"),
            "subcategories": builtin_subs + custom_subs,
            "custom_subcategories": custom_subs,
            "is_custom": False,
        })
        known.add(name)

    for custom in extra.get("categories", []):
        name = custom["name"]
        if name in known:
            continue
        custom_subs = list(extra.get("subcategories", {}).get(name, []))
        result.append({
            "name": name,
            "emoji": custom.get("emoji", "🏷️"),
            "subcategories": custom_subs,
            "custom_subcategories": custom_subs,
            "is_custom": True,
        })
        known.add(name)

    for row in get_all_transactions(household_id):
        cat = str(row.get("category") or "").strip()
        if cat and cat not in known:
            custom_subs = list(extra.get("subcategories", {}).get(cat, []))
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
    extra = _read_extra_categories(household_id)
    cats: list[dict] = extra.setdefault("categories", [])
    if not any(c["name"] == name for c in cats):
        cats.append({"name": name, "emoji": emoji})
        _write_extra_categories(household_id, extra)


def save_custom_subcategory(category_name: str, subcategory: str, *, household_id: int) -> None:
    extra = _read_extra_categories(household_id)
    subs: dict = extra.setdefault("subcategories", {})
    cat_subs: list = subs.setdefault(category_name, [])
    if subcategory not in cat_subs:
        cat_subs.append(subcategory)
        _write_extra_categories(household_id, extra)


def delete_category(name: str, household_id: int) -> bool:
    if not name:
        return False
    extra = _read_extra_categories(household_id)
    if name in CATEGORY_NAMES:
        deleted: list = extra.setdefault("deleted_categories", [])
        if name not in deleted:
            deleted.append(name)
        extra.get("subcategories", {}).pop(name, None)
    else:
        cats = extra.get("categories", [])
        extra["categories"] = [c for c in cats if c["name"] != name]
        extra.get("subcategories", {}).pop(name, None)
    _write_extra_categories(household_id, extra)
    return True


delete_custom_category = delete_category


def delete_custom_subcategory(category_name: str, subcategory: str, household_id: int) -> bool:
    extra = _read_extra_categories(household_id)
    cat_subs: list = extra.get("subcategories", {}).get(category_name, [])
    if subcategory not in cat_subs:
        return False
    cat_subs.remove(subcategory)
    extra.setdefault("subcategories", {})[category_name] = cat_subs
    _write_extra_categories(household_id, extra)
    return True
