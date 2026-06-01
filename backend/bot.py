import asyncio
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta
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

GREETING_REPLY = "👋 Hi! Tell me what you spent or earned.\nEg: Zomato 280 · Petrol 500 · Salary 45000"
AMOUNT_NOT_FOUND_REPLY = "❓ No amount found.\nTry: Petrol 500  or  Salary 45000"
GROQ_FAILED_REPLY = "⚠️ Could not process your message.\nTry: Swiggy 350 dinner"

# Maps (chat_id, bot_message_id) → transaction_id for category-change-via-reply
_msg_transaction_map: dict[tuple[int, int], str] = {}
_MAP_MAX_SIZE = 200


def _store_msg_transaction(chat_id: int, message_id: int, transaction_id: str) -> None:
    _msg_transaction_map[(chat_id, message_id)] = transaction_id
    if len(_msg_transaction_map) > _MAP_MAX_SIZE:
        del _msg_transaction_map[next(iter(_msg_transaction_map))]


def _to_new_category(text: str) -> str:
    """Title-case and trim a user-supplied string for use as a new category name."""
    return " ".join(text.strip().title().split())[:40]


def _parse_category_from_reply(text: str) -> tuple[str | None, str | None]:
    """Parse (category, subcategory) from a reply message.

    Matching order:
    1. "Food > Delivery"  → fuzzy-map left → (Food & Dining, Delivery)
    2. Known subcategory  → "fuel" → (Transport, Fuel)
    3. Fuzzy category     → "health" → (Health & Medical, None)
    4. New category       → "Pet Care" → ("Pet Care", None)  ← created on the fly

    Returns (None, None) only when the input is blank.
    """
    cleaned = re.sub(r"^(change|cat|category|update|set)\s*[:\-]?\s*", "", (text or "").strip(), flags=re.IGNORECASE).strip()
    if not cleaned:
        return None, None

    # "Category > Subcategory" — left side mapped, right side kept as-is
    if ">" in cleaned:
        cat_part, sub_part = (p.strip() for p in cleaned.split(">", 1))
        category = fuzzy_match_category(cat_part) or _to_new_category(cat_part)
        return category, sub_part or None

    # Try fuzzy match against known categories first
    category = fuzzy_match_category(cleaned)
    if category:
        return category, None

    # Try matching as a known subcategory
    lower = cleaned.lower()
    for cat, subs in SUBCATEGORY_MAP.items():
        for sub in subs:
            if sub.lower() == lower or sub.lower().startswith(lower) or lower in sub.lower():
                return cat, sub

    # Nothing matched → treat the reply as a brand-new category name
    return _to_new_category(cleaned), None


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


def single_transaction_reply(item: dict) -> str:
    transaction = item.get("transaction") or item
    category = clean_text(transaction.get("category"))
    emoji = category_emoji(category)
    amount = indian_format(transaction.get("amount"))
    icon = transaction_icon(transaction.get("type"))
    description = clean_text(transaction.get("description")) or "Transaction"
    source = clean_text(transaction.get("source"))
    note = f"{description} · {source}" if source else description
    balance = indian_format(summary_balance())
    return f"{icon} {amount} · {category} {emoji}\n📝 {note}\n🏦 Balance: {balance}"


def transaction_line(transaction: dict) -> str:
    category = clean_text(transaction.get("category"))
    emoji = category_emoji(category)
    icon = transaction_icon(transaction.get("type"))
    amount = indian_format(transaction.get("amount"))
    description = clean_text(transaction.get("description")) or "Transaction"
    source = clean_text(transaction.get("source"))
    tail = f"{description} · {source}" if source else description
    return f"{icon} {amount} · {category} {emoji} · {tail}"


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
        "💡 Reply to any logged transaction to change its category.\n"
        "   Eg: 'Food', 'Transport', or 'Food > Delivery'"
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


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(ChatAction.TYPING)
    text = update.message.text or ""

    # Category change: reply to a previously logged transaction message
    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        if replied.from_user and replied.from_user.is_bot:
            key = (update.message.chat_id, replied.message_id)
            transaction_id = _msg_transaction_map.get(key)
            if transaction_id:
                new_category, new_subcategory = _parse_category_from_reply(text)
                if new_category:
                    patch_payload: dict = {"category": new_category}
                    if new_subcategory is not None:
                        patch_payload["subcategory"] = new_subcategory
                    result = await with_retry(update, api_patch, f"/api/transactions/{transaction_id}", patch_payload)
                    if result:
                        is_new = new_category not in CATEGORY_NAMES
                        emoji = category_emoji(new_category)
                        tag = " ✨ new" if is_new else ""
                        confirm = f"✅ Category → {new_category} {emoji}{tag}"
                        if new_subcategory:
                            confirm += f"\n   Subcategory → {new_subcategory}"
                        await update.message.reply_text(confirm)
                return

    if is_greeting_message(text):
        await update.message.reply_text(GREETING_REPLY)
        return

    parts = split_transaction_message(text)
    saved_items = []
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

    if not saved_items:
        await update.message.reply_text(AMOUNT_NOT_FOUND_REPLY if skipped_no_amount else GROQ_FAILED_REPLY)
    elif len(saved_items) == 1:
        transaction_id = (saved_items[0].get("transaction") or saved_items[0]).get("id")
        sent = await update.message.reply_text(single_transaction_reply(saved_items[0]))
        if transaction_id:
            _store_msg_transaction(update.message.chat_id, sent.message_id, transaction_id)
    else:
        total = sum(float((item.get("transaction") or {}).get("amount", 0)) for item in saved_items)
        await update.message.reply_text(multi_transaction_reply(saved_items, total))


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
    saved_items = []
    total = 0.0
    for item in transactions:
        saved = await with_retry(update, save_extracted, item, "image/pdf upload", input_method, user_info)
        if saved:
            saved_items.append(saved)
            total += float(saved.get("transaction", {}).get("amount", 0))
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
