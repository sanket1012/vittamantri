import asyncio
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

import pytz
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from categories import CATEGORIES, CATEGORY_NAMES, SUBCATEGORY_MAP, category_emoji, fuzzy_match_category

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
_API_HEADERS = {"X-Api-Key": os.getenv("DASHBOARD_API_KEY", "")}
IST = pytz.timezone("Asia/Kolkata")

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("vittamantri.bot")
logging.getLogger("httpx").setLevel(logging.WARNING)

GREETING_REPLY = (
    "👋 Hi! Here's what I can do:\n\n"
    "💸 Log a transaction\n"
    "   Zomato 280  ·  Petrol 500  ·  Salary 45000\n\n"
    "📊 Check your finances\n"
    "   my balance  ·  today's spending  ·  this month\n\n"
    "✏️ Fix a category\n"
    "   update last to Food  ·  reply to any transaction"
)
AMOUNT_NOT_FOUND_REPLY = "❓ No amount found.\nTry: Petrol 500  or  Salary 45000"
GROQ_FAILED_REPLY = (
    "⚠️ I couldn't understand that.\n\n"
    "• Log:    Zomato 280  ·  Petrol 500\n"
    "• Check:  my balance  ·  today  ·  this month\n"
    "• Update: update last to Food"
)

# ── Intent classification ──────────────────────────────────────────────────────


class Intent(str, Enum):
    ADD = "add"          # log a new expense / income
    UPDATE = "update"    # change category of last/recent transaction
    SUMMARY = "summary"  # overall balance or all-time totals
    TODAY = "today"      # today's activity
    WEEK = "week"        # last-7-days activity
    MONTH = "month"      # this-month's activity
    GREET = "greet"      # greeting / small talk
    PARSE = "parse"      # unclear — forward to Groq and let it decide


_QUERY_WORDS = frozenset([
    "balance", "summary", "total", "how much", "spent", "spend",
    "earned", "earn", "saved", "save", "overview", "report",
    "expenses", "expense", "income", "spending", "show", "list",
    "tell me", "what did", "how are", "where did",
])

_TEMPORAL_TODAY = re.compile(r"\btoday\b|\bright now\b")
_TEMPORAL_WEEK  = re.compile(r"\b(this\s+)?week\b|\blast\s+7\s+days?\b")
_TEMPORAL_MONTH = re.compile(r"\b(this\s+)?month\b|\bmonthly\b|\blast\s+30\s+days?\b")
_HAS_AMOUNT     = re.compile(r"(?:₹|rs\.?\s*)?\b\d{2,}(?:[,\d]*)?(?:\.\d+)?\b")


def detect_intent(text: str) -> Intent:
    """Classify the intent of an incoming message before any processing.

    Priority order:
    1. Explicit update-last command
    2. Temporal shortcuts without amounts  (today / week / month)
    3. Query / question signals without amounts  → summary or temporal
    4. Greeting  (checked AFTER specific signals to avoid swallowing "show today")
    5. Message with an amount  → add transaction
    6. Everything else  → forward to Groq parser
    """
    lower = text.lower().strip()
    has_amount = bool(_HAS_AMOUNT.search(lower))

    # 1. Explicit update command — must come before amount check
    if _is_update_last_request(text):
        return Intent.UPDATE

    # 2. Temporal shortcuts — no amount required, just the time word
    if not has_amount:
        if _TEMPORAL_TODAY.search(lower):
            return Intent.TODAY
        if _TEMPORAL_WEEK.search(lower):
            return Intent.WEEK
        if _TEMPORAL_MONTH.search(lower):
            return Intent.MONTH

    # 3. Query / question signals (no amount)
    if not has_amount:
        has_query  = any(kw in lower for kw in _QUERY_WORDS)
        has_q_word = bool(re.search(r"\b(what|how|when|where|show|tell|list|give|my)\b", lower))
        has_qmark  = "?" in text
        if has_query or has_q_word or has_qmark:
            if _TEMPORAL_TODAY.search(lower):
                return Intent.TODAY
            if _TEMPORAL_WEEK.search(lower):
                return Intent.WEEK
            if _TEMPORAL_MONTH.search(lower):
                return Intent.MONTH
            return Intent.SUMMARY

    # 4. Greeting — checked after specific signals
    if is_greeting_message(text):
        return Intent.GREET

    # 5. Has a transaction amount
    if has_amount:
        return Intent.ADD

    # 6. Forward to Groq
    return Intent.PARSE

# Maps (chat_id, bot_message_id) → transaction_id for category-change-via-reply
_msg_transaction_map: dict[tuple[int, int], str] = {}
_MAP_MAX_SIZE = 200

# Maps chat_id → last saved transaction_id (powers "update last transaction" requests)
_last_transaction_map: dict[int, str] = {}


def _store_msg_transaction(chat_id: int, message_id: int, transaction_id: str) -> None:
    _msg_transaction_map[(chat_id, message_id)] = transaction_id
    _last_transaction_map[chat_id] = transaction_id      # always track last
    if len(_msg_transaction_map) > _MAP_MAX_SIZE:
        del _msg_transaction_map[next(iter(_msg_transaction_map))]


def _track_last(chat_id: int, transaction_id: str) -> None:
    """Track last saved transaction without a message mapping (multi-transaction / media)."""
    _last_transaction_map[chat_id] = transaction_id


def _to_new_category(text: str) -> str:
    """Title-case and trim a user-supplied string for use as a new category name."""
    return " ".join(text.strip().title().split())[:40]


def _get_all_categories_from_api() -> list[dict]:
    """Fetch live categories with subcategories (built-in + custom) from the backend. Returns [] on failure."""
    try:
        return api_get("/api/categories/full")
    except Exception as exc:
        logger.warning("Could not load categories from API: %s", exc)
        return []


def _parse_category_from_reply(text: str) -> tuple[str | None, str | None]:
    """Parse (category, subcategory) from a reply message.

    Matching order:
    1. "Food > Delivery"  → fuzzy-map left → (Food & Dining, Delivery)
    2. Known subcategory  → "fuel" → (Transport, Fuel)  — checks built-in + custom
    3. Fuzzy category     → "health" → (Health & Medical, None)
    4. New category       → "Pet Care" → ("Pet Care", None)  ← created on the fly

    Returns (None, None) only when the input is blank.
    """
    cleaned = re.sub(r"^(change|cat|category|update|set)\s*[:\-]?\s*", "", (text or "").strip(), flags=re.IGNORECASE).strip()
    if not cleaned:
        return None, None

    all_cats = _get_all_categories_from_api()
    all_cat_names = [c["name"] for c in all_cats]

    # "Category > Subcategory" — left side mapped, right side kept as-is
    if ">" in cleaned:
        cat_part, sub_part = (p.strip() for p in cleaned.split(">", 1))
        category = fuzzy_match_category(cat_part, extra_names=all_cat_names) or _to_new_category(cat_part)
        return category, sub_part or None

    # Try fuzzy match against all categories (built-in + custom)
    category = fuzzy_match_category(cleaned, extra_names=all_cat_names)
    if category:
        return category, None

    # Try matching as a subcategory — check built-in and custom subcategories
    lower = cleaned.lower()
    for cat_dict in all_cats:
        cat_name = cat_dict["name"]
        for sub in cat_dict.get("subcategories", []):
            if sub.lower() == lower or sub.lower().startswith(lower) or lower in sub.lower():
                return cat_name, sub

    # Nothing matched → treat the reply as a brand-new category name
    return _to_new_category(cleaned), None


def _is_update_last_request(text: str) -> bool:
    """True when the message is a command to update the last transaction's category.

    Detects patterns like:
    - "update last transaction's category to Food"
    - "change the last one to Transport"
    - "set last transaction as Groceries"
    Excludes messages that look like new transactions (contain amounts ≥ 10).
    """
    lower = (text or "").lower().strip()
    has_verb = bool(re.search(r"\b(?:update|change|set|edit|modify)\b", lower))
    has_last = bool(re.search(r"\b(?:last|latest|prev(?:ious)?|recent)\b", lower))
    # If the message contains a plausible transaction amount it's likely a new entry, not a command
    has_amount = bool(re.search(r"(?:₹|rs\.?\s*)?\b\d{2,}\b", lower))
    return has_verb and has_last and not has_amount


def _extract_update_value(text: str) -> str | None:
    """Extract the new category value from an update command.

    Handles: "... to Food", "... as Transport", "... : Groceries", "... = Shopping"
    """
    match = re.search(r"\b(?:to|as)\s+[\"']?(.+?)[\"']?\s*$", text, re.IGNORECASE)
    if match:
        value = re.sub(r"[.,!?]+$", "", match.group(1).strip().strip("\"'"))
        return value or None
    match = re.search(r"[:\=]\s*[\"']?(.+?)[\"']?\s*$", text)
    if match:
        value = re.sub(r"[.,!?]+$", "", match.group(1).strip().strip("\"'"))
        return value or None
    return None


def _is_category_uncertain(category: str, raw_message: str) -> bool:
    """True when category landed on the generic default with no clear justification."""
    if category != "Gifts & Misc":
        return False
    lower = (raw_message or "").lower()
    return not any(kw in lower for kw in ["gift", "gifted", "donation", "donate", "misc", "other", "random"])


def indian_format(amount: float) -> str:
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        amount = 0
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if amount == int(amount):
        s = str(int(amount))
    else:
        whole, decimal = f"{amount:.2f}".split(".")
        s = whole
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)
        parts.reverse()
        formatted = f"{','.join(parts)},{last3}"
    if amount != int(amount):
        formatted = f"{formatted}.{decimal}"
    return f"{sign}₹{formatted}"


def transaction_icon(transaction_type: str) -> str:
    return "💰" if transaction_type == "income" else "💸"


def clean_text(value) -> str:
    return str(value or "").strip()


def telegram_user_info(update: Update) -> dict:
    user = update.effective_user
    if not user:
        return {"logged_by": "Unknown", "logged_by_id": 0}
    logged_by = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if not logged_by:
        logged_by = user.username or f"User_{user.id}"
    return {"logged_by": logged_by, "logged_by_id": user.id}


def api_get(path: str):
    response = requests.get(f"{API_BASE}{path}", headers=_API_HEADERS, timeout=20)
    _raise_for_status(response)
    return response.json()


def api_post(path: str, payload: dict):
    response = requests.post(f"{API_BASE}{path}", json=payload, headers=_API_HEADERS, timeout=20)
    _raise_for_status(response)
    return response.json()


def api_delete(path: str):
    response = requests.delete(f"{API_BASE}{path}", headers=_API_HEADERS, timeout=20)
    _raise_for_status(response)
    return response.json()


def api_patch(path: str, payload: dict):
    response = requests.patch(f"{API_BASE}{path}", json=payload, headers=_API_HEADERS, timeout=20)
    _raise_for_status(response)
    return response.json()


def api_upload(path: str, field_name: str, filename: str, content: bytes, mime_type: str):
    response = requests.post(
        f"{API_BASE}{path}",
        files={field_name: (filename, content, mime_type)},
        headers=_API_HEADERS,
        timeout=60,
    )
    _raise_for_status(response)
    return response.json()


def _raise_for_status(response: requests.Response) -> None:
    if response.ok:
        return
    try:
        detail = response.json().get("error") or response.text
    except ValueError:
        detail = response.text
    raise RuntimeError(f"{response.status_code} from backend: {detail}")


async def with_retry(update: Update, func, *args):
    for attempt in range(2):
        try:
            return func(*args)
        except Exception as exc:
            logger.warning("Retryable operation failed on attempt %s: %s", attempt + 1, exc)
            if attempt == 0:
                await asyncio.sleep(2)
                continue
            await update.effective_message.reply_text("Sorry, I could not process that right now. Please try again.")
            return None


async def parse_text_with_retry(message: str) -> dict | None:
    for attempt in range(2):
        try:
            return api_post("/api/parse/text", {"message": message})
        except Exception as exc:
            logger.warning("Groq text parse failed on attempt %s for %r: %s", attempt + 1, message, exc)
            if attempt == 0:
                await asyncio.sleep(2)
    return None


def is_greeting_message(text: str) -> bool:
    cleaned = re.sub(r"[^\w\s]", " ", text or "", flags=re.UNICODE).strip().lower()
    words = [word for word in cleaned.split() if word]
    return len(words) < 3 and not any(char.isdigit() for char in cleaned)


def split_transaction_message(text: str) -> list[str]:
    chunks = []
    for line in re.split(r"[\r\n;]+", text or ""):
        line = line.strip()
        if not line:
            continue
        parts = re.split(r",\s*(?=[^\d\s])", line)
        chunks.extend(part.strip() for part in parts if part.strip())
    return chunks


def save_extracted(transaction: dict, raw_input: str, input_method: str = "text", user_info: dict | None = None) -> dict | None:
    if not transaction or not transaction.get("amount"):
        return None
    payload = {
        **transaction,
        **(user_info or {"logged_by": "Unknown", "logged_by_id": 0}),
        "input_method": input_method,
        "raw_input": raw_input,
    }
    return api_post("/api/transactions", payload)


def summary_balance() -> float:
    try:
        return float(api_get("/api/summary").get("net_savings", 0))
    except Exception as exc:
        logger.warning("Could not load balance: %s", exc)
        return 0.0


def _cat_display(category: str, subcategory: str | None = None) -> str:
    emoji = category_emoji(category)
    display = f"{category} {emoji}"
    if subcategory:
        display += f" › {subcategory}"
    return display


def single_transaction_reply(item: dict) -> str:
    transaction = item.get("transaction") or item
    category = clean_text(transaction.get("category"))
    subcategory = clean_text(transaction.get("subcategory")) or None
    amount = indian_format(transaction.get("amount"))
    icon = transaction_icon(transaction.get("type"))
    description = clean_text(transaction.get("description")) or "Transaction"
    source = clean_text(transaction.get("source"))
    note = f"{description} · {source}" if source else description
    balance = indian_format(summary_balance())
    return f"{icon} {amount} · {_cat_display(category, subcategory)}\n📝 {note}\n🏦 Balance: {balance}"


def transaction_line(transaction: dict) -> str:
    category = clean_text(transaction.get("category"))
    subcategory = clean_text(transaction.get("subcategory")) or None
    icon = transaction_icon(transaction.get("type"))
    amount = indian_format(transaction.get("amount"))
    description = clean_text(transaction.get("description")) or "Transaction"
    source = clean_text(transaction.get("source"))
    tail = f"{description} · {source}" if source else description
    return f"{icon} {amount} · {_cat_display(category, subcategory)} · {tail}"


def multi_transaction_reply(saved_items: list[dict], total: float) -> str:
    count = len(saved_items)
    lines = [f"✅ {count} transactions logged!", ""]
    show_count = min(5, count)
    for item in saved_items[:show_count]:
        lines.append(transaction_line(item.get("transaction") or item))
    if count > show_count:
        lines.append(f"+ {count - show_count} more logged")
    lines.extend(["", f"💳 Total: {indian_format(total)}", f"🏦 Balance: {indian_format(summary_balance())}"])
    return "\n".join(lines)


def compact_transaction_row(row: dict) -> str:
    icon = transaction_icon(row.get("type"))
    return f"{icon} {indian_format(row.get('amount'))} {row.get('category')} · {row.get('description')}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(GREETING_REPLY)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/summary - combined + per-user totals\n"
        "/me - your personal summary\n"
        "/today - today's list\n"
        "/week - last 7 days\n"
        "/month - this month\n"
        "/export - CSV\n"
        "/delete <id> - delete\n\n"
        "📂 Category tips:\n"
        "• Reply to any logged transaction with a category to update it\n"
        "  Eg: Food  ·  Transport  ·  Food > Delivery\n"
        "• Or just say: update last to Food  ·  change last to Transport > Fuel\n"
        "• Unknown categories are created on the fly ✨"
    )


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    user_info = telegram_user_info(update)
    user_id = user_info.get("logged_by_id", 0)
    data = await with_retry(update, api_get, f"/api/summary/user/{user_id}")
    if not data:
        return
    name = user_info.get("logged_by", "You")
    lines = [
        f"👤 {name}'s Summary\n",
        f"💰 Income:  {indian_format(data.get('total_income'))}",
        f"💸 Expense: {indian_format(data.get('total_expense'))}",
        f"🏦 Balance: {indian_format(data.get('net_savings'))}",
        f"📋 Transactions: {data.get('transaction_count', 0)}",
    ]
    await update.message.reply_text("\n".join(lines))


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    data = await with_retry(update, api_get, "/api/summary")
    if not data:
        return
    users = []
    try:
        users = api_get("/api/users")
    except Exception as exc:
        logger.warning("Could not load user breakdown: %s", exc)
    lines = [
        "📊 Your Summary\n\n"
        f"💰 Income:  {indian_format(data.get('total_income'))}\n"
        f"💸 Expense: {indian_format(data.get('total_expense'))}\n"
        f"🏦 Balance: {indian_format(data.get('net_savings'))}\n"
        f"📋 Total: {data.get('transaction_count', 0)} transactions"
    ]
    if len(users) >= 1:
        lines.append("\n👥 By User:")
        transactions = api_get("/api/transactions").get("transactions", [])
        for user in users[:5]:
            uid = str(user.get("logged_by_id"))
            user_rows = [row for row in transactions if str(row.get("logged_by_id")) == uid]
            spent = sum(float(row.get("amount", 0)) for row in user_rows if row.get("type") == "expense")
            earned = sum(float(row.get("amount", 0)) for row in user_rows if row.get("type") == "income")
            lines.append(
                f"- {user.get('logged_by')}: "
                f"💰 {indian_format(earned)} in · 💸 {indian_format(spent)} out"
            )
    await update.message.reply_text("\n".join(lines))


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    data = await with_retry(update, api_get, "/api/transactions")
    if not data:
        return
    today_key = datetime.now(IST).strftime("%Y-%m-%d")
    rows = [row for row in data.get("transactions", []) if row.get("date") == today_key]
    if not rows:
        await update.message.reply_text("📅 Today · 0 transactions")
        return
    spent = sum(float(row.get("amount", 0)) for row in rows if row.get("type") == "expense")
    earned = sum(float(row.get("amount", 0)) for row in rows if row.get("type") == "income")
    lines = [f"📅 Today · {len(rows)} transactions", ""]
    lines += [f"{compact_transaction_row(row)} [{row.get('logged_by') or 'Unknown'}]" for row in rows[:5]]
    lines += ["", f"💸 Spent: {indian_format(spent)}", f"💰 Earned: {indian_format(earned)}"]
    await update.message.reply_text("\n".join(lines))


def category_totals_for_rows(rows: list[dict]) -> dict[str, float]:
    totals = {}
    for row in rows:
        if row.get("type") == "expense":
            category = row.get("category") or "Other"
            totals[category] = totals.get(category, 0.0) + float(row.get("amount", 0))
    return totals


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    data = await with_retry(update, api_get, "/api/transactions")
    if not data:
        return
    start_day = datetime.now(IST).date() - timedelta(days=7)
    rows = []
    for row in data.get("transactions", []):
        try:
            if datetime.strptime(row.get("date", ""), "%Y-%m-%d").date() >= start_day:
                rows.append(row)
        except ValueError:
            continue
    await send_period_summary(update, "🗓️ Last 7 Days", rows)


async def month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    data = await with_retry(update, api_get, "/api/transactions")
    if not data:
        return
    month_key = datetime.now(IST).strftime("%Y-%m")
    rows = [row for row in data.get("transactions", []) if str(row.get("date", "")).startswith(month_key)]
    await send_period_summary(update, f"📆 {datetime.now(IST).strftime('%B %Y')}", rows)


async def send_period_summary(update: Update, title: str, rows: list[dict]):
    totals = category_totals_for_rows(rows)
    if not totals:
        await update.message.reply_text(f"{title}\n\nNo spending found.")
        return
    sorted_totals = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    lines = [title, ""]
    for category, amount in sorted_totals[:5]:
        lines.append(f"{category_emoji(category)} {category:<16} {indian_format(amount)}")
    total_spent = sum(totals.values())
    lines.extend(["", f"💸 Total Spent: {indian_format(total_spent)}"])
    await update.message.reply_text("\n".join(lines))


async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\n".join(f"{meta['emoji']} {name}" for name, meta in CATEGORIES.items()))


async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    try:
        response = requests.get(f"{API_BASE}/api/export/csv", headers=_API_HEADERS, timeout=20)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp:
            temp.write(response.content)
            temp_path = temp.name
        await update.message.reply_document(document=Path(temp_path), filename="transactions.csv")
        Path(temp_path).unlink(missing_ok=True)
    except Exception as exc:
        logger.warning("CSV export failed: %s", exc)
        await update.message.reply_text("Could not export CSV right now.")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Send /delete <id>")
        return
    result = await with_retry(update, api_delete, f"/api/transactions/{context.args[0]}")
    if result:
        await update.message.reply_text("✅ Deleted")


async def _apply_category_update(update: Update, transaction_id: str, text: str) -> bool:
    """Parse *text* as a category/subcategory update and apply it.  Returns True on success."""
    new_category, new_subcategory = _parse_category_from_reply(text)
    if not new_category:
        return False
    patch_payload: dict = {"category": new_category}
    if new_subcategory is not None:
        patch_payload["subcategory"] = new_subcategory
    result = await with_retry(update, api_patch, f"/api/transactions/{transaction_id}", patch_payload)
    if result:
        is_new = new_category not in CATEGORY_NAMES
        tag = " ✨ new" if is_new else ""
        confirm = f"✅ Category → {_cat_display(new_category, new_subcategory)}{tag}"
        await update.message.reply_text(confirm)
    return True


async def _handle_update_last(update: Update, text: str) -> None:
    """Handle 'update last transaction to X' commands."""
    chat_id = update.message.chat_id
    transaction_id = _last_transaction_map.get(chat_id)
    if not transaction_id:
        await update.message.reply_text(
            "❓ No recent transaction found in this chat to update.\n"
            "Log a transaction first, then ask to update it."
        )
        return
    value_text = _extract_update_value(text)
    if not value_text:
        await update.message.reply_text(
            "❓ Could not find the new category in your message.\n"
            "Try: update last to Food  ·  change last to Transport > Fuel"
        )
        return
    await _apply_category_update(update, transaction_id, value_text)


async def _handle_add_transaction(update: Update, text: str) -> None:
    """Parse and save one or more transactions from a free-text message."""
    chat_id = update.message.chat_id
    parts = split_transaction_message(text)
    saved_items: list[dict] = []
    skipped_no_amount = False

    for part in parts:
        parsed = await parse_text_with_retry(part)
        if not parsed:
            continue
        extracted = parsed.get("transaction", {})
        if not extracted.get("amount"):
            skipped_no_amount = True
            continue
        saved = await with_retry(update, save_extracted, extracted, part, "text", telegram_user_info(update))
        if saved:
            saved_items.append(saved)
            txn_id = (saved.get("transaction") or saved).get("id")
            if txn_id:
                _track_last(chat_id, txn_id)

    if not saved_items:
        await update.message.reply_text(AMOUNT_NOT_FOUND_REPLY if skipped_no_amount else GROQ_FAILED_REPLY)
    elif len(saved_items) == 1:
        item = saved_items[0]
        txn = item.get("transaction") or item
        reply_text = single_transaction_reply(item)
        if _is_category_uncertain(txn.get("category", ""), parts[0] if parts else text):
            reply_text += "\n\n❓ Category unclear — reply with the right one (e.g. Food, Transport, Shopping)"
        sent = await update.message.reply_text(reply_text)
        if txn.get("id"):
            _store_msg_transaction(chat_id, sent.message_id, txn["id"])
    else:
        total = sum(float((item.get("transaction") or {}).get("amount", 0)) for item in saved_items)
        await update.message.reply_text(multi_transaction_reply(saved_items, total))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    text = (update.message.text or "").strip()
    chat_id = update.message.chat_id

    # ── 0. Reply to a bot message always triggers a category update ──────────
    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        if replied.from_user and replied.from_user.is_bot:
            key = (chat_id, replied.message_id)
            txn_id = _msg_transaction_map.get(key) or _last_transaction_map.get(chat_id)
            if txn_id:
                await _apply_category_update(update, txn_id, text)
                return

    # ── 1. Classify intent ────────────────────────────────────────────────────
    intent = detect_intent(text)
    logger.info("intent=%s  msg=%r", intent, text[:60])

    # ── 2. Route ──────────────────────────────────────────────────────────────
    if intent == Intent.GREET:
        await update.message.reply_text(GREETING_REPLY)

    elif intent == Intent.UPDATE:
        await _handle_update_last(update, text)

    elif intent == Intent.SUMMARY:
        await summary(update, context)

    elif intent == Intent.TODAY:
        await today(update, context)

    elif intent == Intent.WEEK:
        await week(update, context)

    elif intent == Intent.MONTH:
        await month(update, context)

    else:  # Intent.ADD or Intent.PARSE — let Groq sort it out
        await _handle_add_transaction(update, text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        telegram_file = await update.message.photo[-1].get_file()
        image_bytes = bytes(await telegram_file.download_as_bytearray())
        parsed = await with_retry(update, api_upload, "/api/parse/image", "image", "receipt.jpg", image_bytes, "image/jpeg")
        if not parsed:
            return
        await save_media_transactions(update, parsed.get("transactions", []), "image", telegram_user_info(update))
    except Exception as exc:
        logger.warning("Image processing failed: %s", exc)
        await update.message.reply_text("Could not process image right now.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or document.mime_type != "application/pdf":
        await update.message.reply_text("Please send a PDF document.")
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        telegram_file = await document.get_file()
        pdf_bytes = bytes(await telegram_file.download_as_bytearray())
        parsed = await with_retry(update, api_upload, "/api/parse/pdf", "pdf", document.file_name or "statement.pdf", pdf_bytes, "application/pdf")
        if not parsed:
            return
        await save_media_transactions(update, parsed.get("transactions", []), "pdf", telegram_user_info(update))
    except Exception as exc:
        logger.warning("PDF processing failed: %s", exc)
        await update.message.reply_text("Could not process PDF right now.")


async def save_media_transactions(update: Update, transactions: list[dict], input_method: str, user_info: dict):
    chat_id = update.message.chat_id
    saved_items = []
    total = 0.0
    for item in transactions:
        saved = await with_retry(update, save_extracted, item, "image/pdf upload", input_method, user_info)
        if saved:
            saved_items.append(saved)
            total += float(saved.get("transaction", {}).get("amount", 0))
            txn_id = (saved.get("transaction") or saved).get("id")
            if txn_id:
                _track_last(chat_id, txn_id)
    if saved_items:
        await update.message.reply_text(multi_transaction_reply(saved_items, total))
    else:
        await update.message.reply_text("No transactions found.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("Telegram bot error: %s", context.error)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured in .env.")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("me", me))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("week", week))
    application.add_handler(CommandHandler("month", month))
    application.add_handler(CommandHandler("categories", categories))
    application.add_handler(CommandHandler("export", export))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)
    application.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
