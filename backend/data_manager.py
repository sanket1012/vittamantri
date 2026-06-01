"""CSV and JSON storage for VittaMantri."""

from __future__ import annotations

import csv
import io
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytz

from categories import CATEGORIES, CATEGORY_NAMES, DEFAULT_CATEGORY, SUBCATEGORY_MAP, infer_category

IST = pytz.timezone("Asia/Kolkata")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
SUMMARY_FILE = DATA_DIR / "summary.json"
CATEGORIES_EXTRA_FILE = DATA_DIR / "categories_extra.json"
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
_lock = threading.Lock()


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


def ensure_data_files() -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not TRANSACTIONS_FILE.exists():
            with TRANSACTIONS_FILE.open("w", newline="", encoding="utf-8") as file:
                csv.DictWriter(file, fieldnames=CSV_COLUMNS).writeheader()
        else:
            _migrate_transactions_file()
        if not SUMMARY_FILE.exists():
            _write_summary(_empty_summary())
    except OSError as exc:
        raise RuntimeError(f"Unable to initialize data files: {exc}") from exc


def _migrate_transactions_file() -> None:
    with TRANSACTIONS_FILE.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames == CSV_COLUMNS:
            return
        rows = list(reader)
    with TRANSACTIONS_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            migrated = {column: row.get(column, "") for column in CSV_COLUMNS}
            writer.writerow(migrated)


def _write_summary(summary: dict[str, Any]) -> None:
    with SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)


def _read_rows_unlocked() -> list[dict[str, str]]:
    ensure_data_files()
    with TRANSACTIONS_FILE.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_rows_unlocked(rows: list[dict[str, Any]]) -> None:
    ensure_data_files()
    with TRANSACTIONS_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows([{column: row.get(column, "") for column in CSV_COLUMNS} for row in rows])


def _as_float(value: Any) -> float:
    try:
        return round(float(str(value).replace(",", "").strip()), 2)
    except (TypeError, ValueError):
        return 0.0


def _short_description(value: Any) -> str:
    words = str(value or "Transaction").strip().split()
    return " ".join(words[:8]) if words else "Transaction"


def _normalize_date(value: Any) -> str:
    if value:
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
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

    return {
        "id": str(data.get("id") or uuid4()),
        "date": _normalize_date(data.get("date")),
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
    item = {column: row.get(column, "") for column in CSV_COLUMNS}
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


def _recalculate_summary_unlocked(rows: list[dict[str, Any]]) -> dict[str, Any]:
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
    summary["category_totals"] = {key: round(value, 2) for key, value in sorted(summary["category_totals"].items())}
    summary["monthly_totals"] = {
        key: {"income": round(value.get("income", 0.0), 2), "expense": round(value.get("expense", 0.0), 2)}
        for key, value in sorted(summary["monthly_totals"].items())
    }
    summary["last_updated"] = _now_ist().replace(microsecond=0).isoformat()
    _write_summary(summary)
    return summary


def save_transaction(data: dict[str, Any]) -> str:
    try:
        row = _normalize_transaction(data)
        with _lock:
            rows = _read_rows_unlocked()
            rows.append(row)
            _write_rows_unlocked(rows)
            _recalculate_summary_unlocked(rows)
        return row["id"]
    except Exception as exc:
        raise RuntimeError(f"Unable to save transaction: {exc}") from exc


def get_all_transactions() -> list[dict[str, Any]]:
    try:
        rows = _read_rows_unlocked()
        return sorted((_public_row(row) for row in rows), key=lambda row: (row["date"], row["time"]), reverse=True)
    except Exception as exc:
        raise RuntimeError(f"Unable to read transactions: {exc}") from exc


def get_transactions_by_month(year: int, month: int) -> list[dict[str, Any]]:
    prefix = f"{year:04d}-{month:02d}"
    return [row for row in get_all_transactions() if str(row.get("date", "")).startswith(prefix)]


def get_transactions_by_category(category: str) -> list[dict[str, Any]]:
    return [row for row in get_all_transactions() if row.get("category") == category]


def get_transactions_by_user(logged_by_id: int) -> list[dict[str, Any]]:
    user_id = str(logged_by_id)
    return [row for row in get_all_transactions() if str(row.get("logged_by_id") or "0") == user_id]


def get_all_users() -> list[dict[str, Any]]:
    users: dict[str, dict[str, Any]] = {}
    for row in get_all_transactions():
        user_id = str(row.get("logged_by_id") or "0")
        name = row.get("logged_by") or "Unknown"
        users.setdefault(user_id, {"logged_by": name, "logged_by_id": int(user_id) if user_id.isdigit() else 0, "count": 0})
        users[user_id]["logged_by"] = name
        users[user_id]["count"] += 1
    return sorted(users.values(), key=lambda item: item["logged_by"].lower())


def get_user_summary(logged_by_id: int) -> dict[str, Any]:
    return _summary_from_rows(get_transactions_by_user(logged_by_id))


def get_categories() -> list[dict[str, str]]:
    names = set(CATEGORY_NAMES)
    for row in get_all_transactions():
        category = str(row.get("category") or "").strip()
        if category:
            names.add(category)
    return [
        {"name": name, "emoji": CATEGORIES.get(name, {}).get("emoji", "🏷️")}
        for name in sorted(names)
    ]


def get_summary() -> dict[str, Any]:
    try:
        ensure_data_files()
        with SUMMARY_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        with _lock:
            return _recalculate_summary_unlocked(_read_rows_unlocked())


def rebuild_summary() -> dict[str, Any]:
    with _lock:
        return _recalculate_summary_unlocked(_read_rows_unlocked())


def update_transaction_category(id: str, category: str) -> bool:
    return update_transaction_fields(id, {"category": category})


_MUTABLE_FIELDS = {"category", "subcategory", "description", "source", "type", "amount", "date"}


def _normalize_field(key: str, value: Any) -> str | None:
    """Normalize and validate a single mutable field value. Returns None to skip."""
    if key == "amount":
        amount = _as_float(value)
        return f"{amount:.2f}" if amount > 0 else None
    if key == "date":
        return _normalize_date(value)
    if key == "type":
        val = str(value).lower().strip()
        return val if val in {"income", "expense"} else None
    return str(value).strip()


def update_transaction_fields(id: str, fields: dict[str, Any]) -> bool:
    normalized = {k: _normalize_field(k, v) for k, v in fields.items() if k in _MUTABLE_FIELDS}
    normalized = {k: v for k, v in normalized.items() if v is not None}
    if not normalized:
        return False
    try:
        with _lock:
            rows = _read_rows_unlocked()
            for row in rows:
                if row.get("id") == id:
                    row.update(normalized)
                    _write_rows_unlocked(rows)
                    _recalculate_summary_unlocked(rows)
                    return True
            return False
    except Exception as exc:
        raise RuntimeError(f"Unable to update transaction: {exc}") from exc


def bulk_update_transactions(ids: list[str], fields: dict[str, Any]) -> int:
    """Apply *fields* to every transaction whose id is in *ids*. Returns updated count."""
    normalized = {k: _normalize_field(k, v) for k, v in fields.items() if k in _MUTABLE_FIELDS}
    normalized = {k: v for k, v in normalized.items() if v is not None}
    if not normalized or not ids:
        return 0
    id_set = set(ids)
    try:
        with _lock:
            rows = _read_rows_unlocked()
            count = sum(1 for row in rows if row.get("id") in id_set)
            if not count:
                return 0
            for row in rows:
                if row.get("id") in id_set:
                    row.update(normalized)
            _write_rows_unlocked(rows)
            _recalculate_summary_unlocked(rows)
            return count
    except Exception as exc:
        raise RuntimeError(f"Unable to bulk update transactions: {exc}") from exc


# ── Custom categories ─────────────────────────────────────────────────────────

def _read_extra_categories() -> dict[str, Any]:
    if not CATEGORIES_EXTRA_FILE.exists():
        return {"categories": [], "subcategories": {}}
    try:
        with CATEGORIES_EXTRA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {"categories": [], "subcategories": {}}


def _write_extra_categories(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CATEGORIES_EXTRA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_categories_with_subcategories() -> list[dict[str, Any]]:
    """Return all categories with subcategories.

    Each entry includes:
    - subcategories: all subs (built-in + custom)
    - custom_subcategories: only user-added subs (these can be deleted)
    - is_custom: True for categories not in the built-in CATEGORY_NAMES list
    """
    extra = _read_extra_categories()
    result: list[dict[str, Any]] = []
    known: set[str] = set()

    for name in CATEGORY_NAMES:
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

    for row in get_all_transactions():
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


def save_custom_category(name: str, emoji: str = "🏷️") -> None:
    extra = _read_extra_categories()
    cats: list[dict] = extra.setdefault("categories", [])
    if not any(c["name"] == name for c in cats):
        cats.append({"name": name, "emoji": emoji})
        _write_extra_categories(extra)


def save_custom_subcategory(category_name: str, subcategory: str) -> None:
    extra = _read_extra_categories()
    subs: dict = extra.setdefault("subcategories", {})
    cat_subs: list = subs.setdefault(category_name, [])
    if subcategory not in cat_subs:
        cat_subs.append(subcategory)
        _write_extra_categories(extra)


def delete_custom_category(name: str) -> bool:
    """Delete a user-created category. Built-in categories cannot be deleted this way."""
    extra = _read_extra_categories()
    cats = extra.get("categories", [])
    updated = [c for c in cats if c["name"] != name]
    if len(updated) == len(cats):
        return False
    extra["categories"] = updated
    extra.get("subcategories", {}).pop(name, None)
    _write_extra_categories(extra)
    return True


def delete_custom_subcategory(category_name: str, subcategory: str) -> bool:
    """Delete a user-added subcategory. Returns False if not found in the custom list."""
    extra = _read_extra_categories()
    cat_subs: list = extra.get("subcategories", {}).get(category_name, [])
    if subcategory not in cat_subs:
        return False
    cat_subs.remove(subcategory)
    extra.setdefault("subcategories", {})[category_name] = cat_subs
    _write_extra_categories(extra)
    return True


def delete_transaction(id: str) -> bool:
    try:
        with _lock:
            rows = _read_rows_unlocked()
            remaining = [row for row in rows if row.get("id") != id]
            if len(remaining) == len(rows):
                return False
            _write_rows_unlocked(remaining)
            _recalculate_summary_unlocked(remaining)
            return True
    except Exception as exc:
        raise RuntimeError(f"Unable to delete transaction: {exc}") from exc


def clean_garbage() -> int:
    try:
        with _lock:
            rows = _read_rows_unlocked()
            clean_rows = [row for row in rows if not _is_garbage_row(row)]
            deleted_count = len(rows) - len(clean_rows)
            if deleted_count:
                _write_rows_unlocked(clean_rows)
            _recalculate_summary_unlocked(clean_rows)
            return deleted_count
    except Exception as exc:
        raise RuntimeError(f"Unable to clean garbage transactions: {exc}") from exc


def export_monthly_report(year: int, month: int) -> str:
    try:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in get_transactions_by_month(year, month):
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})
        return output.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Unable to export monthly report: {exc}") from exc


def transaction_csv_path() -> Path:
    ensure_data_files()
    return TRANSACTIONS_FILE


ensure_data_files()
