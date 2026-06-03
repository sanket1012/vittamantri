import logging
import os
import io
import asyncio
import datetime
from dotenv import load_dotenv

load_dotenv()

from google import genai
from groq import Groq
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import finance_db
import finance_extractor
import finance_dashboard
import assistant
import advisor

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def _load_authorized_ids() -> set[int]:
    # Support both AUTHORIZED_USER_IDS (comma-separated) and legacy AUTHORIZED_USER_ID
    ids_str = os.environ.get("AUTHORIZED_USER_IDS") or os.environ.get("AUTHORIZED_USER_ID", "0")
    return {int(uid.strip()) for uid in ids_str.split(",") if uid.strip()}

AUTHORIZED_IDS = _load_authorized_ids()
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://localhost:8080")

gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])


def is_authorized(update: Update) -> bool:
    if 0 in AUTHORIZED_IDS:
        return True
    return update.effective_user.id in AUTHORIZED_IDS


def today() -> str:
    return datetime.date.today().isoformat()


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _save_transactions(user_id: int, transactions: list[dict], source: str) -> None:
    loop = asyncio.get_event_loop()
    for t in transactions:
        await loop.run_in_executor(
            None,
            finance_db.add_transaction,
            user_id,
            t.get("date", today()),
            float(t["amount"]),
            t["type"],
            t["category"],
            t.get("description", ""),
            source,
        )


async def _get_categories(user_id: int) -> list[str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, finance_db.get_all_categories, user_id)


# ── Commands ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "Hey Sanket! I'm your personal assistant + finance tracker.\n\n"
        "<b>Finance commands:</b>\n"
        "/balance [YYYY-MM]       — balance sheet for a month\n"
        "/history [N]             — last N transactions (default 10)\n"
        "/report [YYYY-MM]        — same as /balance\n"
        "/undo                    — delete last recorded transaction\n"
        "/categories              — list all categories used\n"
        "/recurring               — list recurring transactions\n"
        "/cancelrecurring &lt;id&gt;    — stop a recurring entry\n\n"
        "<b>Advisor &amp; Planning:</b>\n"
        "/advisor [question]      — CA financial advisor with your live data\n"
        "/goals                   — view financial goals\n"
        "/cancelgoal &lt;id&gt;         — remove a goal\n"
        "/plans                   — view planned future expenses\n"
        "/cancelplan &lt;id&gt;         — remove a plan\n\n"
        "<b>General:</b>\n"
        "/clear — reset conversation memory\n"
        "/help  — show this message\n\n"
        "Just talk naturally — I detect transactions, recurring entries, goals, and plans automatically.",
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    assistant.clear_history(update.effective_user.id)
    await update.message.reply_text("Conversation memory cleared.")


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    month = context.args[0] if context.args else datetime.date.today().strftime("%Y-%m")

    loop = asyncio.get_event_loop()
    summary = await loop.run_in_executor(None, finance_db.get_summary, user_id, month)
    text = finance_dashboard.build_summary_text(summary, month, DASHBOARD_URL)
    await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await balance_command(update, context)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    try:
        limit = min(int(context.args[0]), 50) if context.args else 10
    except ValueError:
        limit = 10
    month = datetime.date.today().strftime("%Y-%m")

    loop = asyncio.get_event_loop()
    txns = await loop.run_in_executor(None, finance_db.get_transactions, user_id, month, limit)
    text = finance_dashboard.build_history_text(txns)
    await update.message.reply_text(text, parse_mode="HTML")


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    loop = asyncio.get_event_loop()
    tx_id = await loop.run_in_executor(None, finance_db.get_last_transaction_id, user_id)
    if tx_id is None:
        await update.message.reply_text("No transactions to undo.")
        return
    deleted = await loop.run_in_executor(None, finance_db.soft_delete_transaction, tx_id)
    if deleted:
        await update.message.reply_text(f"Undone: transaction #{tx_id} removed.")
    else:
        await update.message.reply_text("Nothing to undo.")


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    loop = asyncio.get_event_loop()
    summary = await loop.run_in_executor(None, finance_db.get_summary, user_id, None)
    cats = summary["by_category"]
    if not cats:
        await update.message.reply_text("No categories recorded yet.")
        return
    lines = ["<b>All Categories</b>", ""]
    for c in cats:
        sign = "-" if c["type"] == "expense" else "+"
        lines.append(f"  {c['category']:<20} {sign}₹{c['total']:>10,.0f}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ── Message handlers ───────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    user_text = update.message.text

    logger.info("[%s | %s] >>> %s", user_id, username, user_text)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Try finance extraction first
    categories = await _get_categories(user_id)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, finance_extractor.extract_from_text,
        user_text, today(), categories, groq_client,
    )

    transactions = [t for t in result.get("transactions", []) if t.get("confidence") != "low"]
    goals_detected = result.get("goals", [])
    plans_detected = result.get("plans", [])

    if transactions or goals_detected or plans_detected:
        loop2 = asyncio.get_event_loop()
        one_time = [t for t in transactions if not t.get("recurring")]
        recurring = [t for t in transactions if t.get("recurring") and t.get("frequency")]
        reply_parts = []

        if one_time:
            await _save_transactions(user_id, one_time, "text")
        for t in recurring:
            await loop2.run_in_executor(
                None, finance_db.add_recurring,
                user_id, float(t["amount"]), t["type"], t["category"],
                t.get("description", ""), t["frequency"], today(),
            )
        if one_time or recurring:
            reply_parts.append(finance_dashboard.build_confirmation_text(one_time + recurring, recurring_ids=[t["frequency"] for t in recurring]))

        for g in goals_detected:
            await loop2.run_in_executor(
                None, finance_db.add_goal,
                user_id, g["name"], float(g["target_amount"]),
                g.get("target_date"), g.get("category", "Savings"), "",
            )
            reply_parts.append(f"🎯 Goal set: <b>{g['name']}</b> — ₹{float(g['target_amount']):,.0f}" +
                                (f" by {g['target_date']}" if g.get("target_date") else ""))

        for p in plans_detected:
            await loop2.run_in_executor(
                None, finance_db.add_plan,
                user_id, p["name"], float(p["amount"]),
                p["planned_date"], p.get("category", "General"), p.get("notes", ""),
            )
            reply_parts.append(f"📅 Plan saved: <b>{p['name']}</b> — ₹{float(p['amount']):,.0f} on {p['planned_date']}")

        reply = "\n".join(reply_parts)
        logger.info("[%s | %s] <<< (finance) %s", user_id, username, reply)
        await update.message.reply_text(reply, parse_mode="HTML")
        return

    # Fall through to general chat
    try:
        reply = assistant.chat(user_id, user_text)
        logger.info("[%s | %s] <<< %s", user_id, username, reply)
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        logger.error("Groq error: %s", e)
        await update.message.reply_text("Sorry, something went wrong. Try again in a moment.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    photo = update.message.photo[-1]  # highest resolution
    tg_file = await context.bot.get_file(photo.file_id)
    buf = io.BytesIO()
    await tg_file.download_to_memory(buf)
    image_bytes = buf.getvalue()

    caption = update.message.caption  # text sent alongside the photo
    categories = await _get_categories(user_id)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, finance_extractor.extract_from_image_bytes,
        image_bytes, "image/jpeg", today(), categories, gemini_client, caption,
    )

    transactions = result.get("transactions", [])
    if not transactions:
        await update.message.reply_text("No transactions found in this image — try a clearer photo.")
        return

    await _save_transactions(user_id, transactions, "image")
    reply = finance_dashboard.build_confirmation_text(transactions)
    await update.message.reply_text(reply)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    doc = update.message.document

    if doc.mime_type != "application/pdf":
        await update.message.reply_text("Only PDF documents are supported for transaction extraction.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_document")

    tg_file = await context.bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await tg_file.download_to_memory(buf)
    pdf_bytes = buf.getvalue()

    categories = await _get_categories(user_id)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, finance_extractor.extract_from_pdf_bytes,
        pdf_bytes, today(), categories, groq_client, gemini_client,
    )

    transactions = result.get("transactions", [])
    if not transactions:
        await update.message.reply_text("No transactions found in this PDF.")
        return

    await _save_transactions(user_id, transactions, "pdf")
    n = len(transactions)
    await update.message.reply_text(
        f"Found {n} transaction{'s' if n != 1 else ''} in the PDF.\n"
        f"Use /balance to see your updated summary."
    )


# ── Recurring commands ─────────────────────────────────────────────────────────

async def recurring_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    loop = asyncio.get_event_loop()
    entries = await loop.run_in_executor(None, finance_db.get_recurring, user_id)
    if not entries:
        await update.message.reply_text(
            "No recurring transactions set up.\n\n"
            "Just tell me naturally, e.g.:\n"
            "<i>\"Pay 5000 rent every month\"</i> or <i>\"Weekly transport 500\"</i>",
            parse_mode="HTML",
        )
        return
    lines = ["<b>Recurring Transactions</b>", ""]
    for e in entries:
        sign = "-" if e["type"] == "expense" else "+"
        lines.append(
            f"[{e['id']}] {sign}₹{e['amount']:,.0f} · {e['category']} · "
            f"{e['frequency']} · next: {e['next_run']}"
        )
    lines += ["", "Use /cancelrecurring &lt;id&gt; to stop one."]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cancelrecurring_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /cancelrecurring <id>  (get IDs from /recurring)")
        return
    try:
        rec_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID. Use /recurring to see IDs.")
        return
    loop = asyncio.get_event_loop()
    deleted = await loop.run_in_executor(None, finance_db.cancel_recurring, rec_id, user_id)
    if deleted:
        await update.message.reply_text(f"Recurring #{rec_id} cancelled.")
    else:
        await update.message.reply_text(f"No active recurring entry #{rec_id} found.")


# ── Daily recurring scheduler ──────────────────────────────────────────────────

async def process_recurring(context) -> None:
    due = finance_db.get_due_recurring(today())
    if not due:
        return

    for entry in due:
        finance_db.add_transaction(
            user_id=entry["user_id"],
            date_=today(),
            amount=entry["amount"],
            type_=entry["type"],
            category=entry["category"],
            description=entry["description"],
            source="recurring",
        )
        finance_db.advance_recurring(entry["id"], entry["next_run"], entry["frequency"])

        # Notify the user
        sign = "-" if entry["type"] == "expense" else "+"
        try:
            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=f"🔁 Auto-recorded: {sign}₹{entry['amount']:,.0f} · {entry['category']}"
                     f" · {entry['description'] or entry['frequency']}",
            )
        except Exception as e:
            logger.warning("Could not notify user %s for recurring: %s", entry["user_id"], e)

    logger.info("Processed %d recurring transaction(s)", len(due))


# ── Advisor command ────────────────────────────────────────────────────────────

async def advisor_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    question = " ".join(context.args) if context.args else "Give me a financial health summary and your top recommendation for this month."

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    loop = asyncio.get_event_loop()
    ctx = await loop.run_in_executor(None, finance_db.get_advisor_context, user_id)
    try:
        reply = await loop.run_in_executor(None, advisor.advise, user_id, question, ctx, groq_client)
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        logger.error("Advisor error: %s", e)
        await update.message.reply_text("Advisor is unavailable right now. Try again in a moment.")


# ── Goals commands ─────────────────────────────────────────────────────────────

async def goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    loop = asyncio.get_event_loop()
    goals = await loop.run_in_executor(None, finance_db.get_goals, user_id, "active")
    if not goals:
        await update.message.reply_text(
            "No active goals yet.\n\nSet one naturally, e.g.:\n"
            "<i>\"Save 200000 for vacation by December\"</i>\n"
            "<i>\"Goal: emergency fund of 300000\"</i>",
            parse_mode="HTML",
        )
        return
    lines = ["<b>Financial Goals</b>", ""]
    for g in goals:
        date_str = f" · by {g['target_date']}" if g.get("target_date") else ""
        lines.append(f"[{g['id']}] <b>{g['name']}</b>{date_str}")
        lines.append(f"     Target: ₹{g['target_amount']:,.0f} · {g['category']}")
        if g.get("notes"):
            lines.append(f"     {g['notes']}")
    lines += ["", "Use /cancelgoal &lt;id&gt; to remove one."]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cancelgoal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /cancelgoal <id>  (get IDs from /goals)")
        return
    try:
        goal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID.")
        return
    loop = asyncio.get_event_loop()
    ok = await loop.run_in_executor(None, finance_db.cancel_goal, goal_id, user_id)
    await update.message.reply_text(f"Goal #{goal_id} cancelled." if ok else f"No active goal #{goal_id} found.")


# ── Plans commands ─────────────────────────────────────────────────────────────

async def plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    loop = asyncio.get_event_loop()
    plans = await loop.run_in_executor(None, finance_db.get_plans, user_id, "pending")
    if not plans:
        await update.message.reply_text(
            "No planned expenses yet.\n\nAdd one naturally, e.g.:\n"
            "<i>\"Planning to buy a laptop for 80000 in June\"</i>\n"
            "<i>\"Car servicing 8000 next month\"</i>",
            parse_mode="HTML",
        )
        return
    lines = ["<b>Planned Expenses</b>", ""]
    total = sum(p["amount"] for p in plans)
    for p in plans:
        lines.append(f"[{p['id']}] <b>{p['name']}</b> · ₹{p['amount']:,.0f} · {p['planned_date']}")
        lines.append(f"     {p['category']}" + (f" · {p['notes']}" if p.get("notes") else ""))
    lines += ["", f"Total planned: ₹{total:,.0f}", "", "Use /cancelplan &lt;id&gt; to remove one."]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cancelplan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /cancelplan <id>  (get IDs from /plans)")
        return
    try:
        plan_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID.")
        return
    loop = asyncio.get_event_loop()
    ok = await loop.run_in_executor(None, finance_db.cancel_plan, plan_id, user_id)
    await update.message.reply_text(f"Plan #{plan_id} cancelled." if ok else f"No pending plan #{plan_id} found.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    finance_db.init_db()

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start",            start))
    app.add_handler(CommandHandler("help",             help_command))
    app.add_handler(CommandHandler("clear",            clear))
    app.add_handler(CommandHandler("balance",          balance_command))
    app.add_handler(CommandHandler("report",           report_command))
    app.add_handler(CommandHandler("history",          history_command))
    app.add_handler(CommandHandler("undo",             undo_command))
    app.add_handler(CommandHandler("categories",       categories_command))
    app.add_handler(CommandHandler("recurring",        recurring_command))
    app.add_handler(CommandHandler("cancelrecurring",  cancelrecurring_command))
    app.add_handler(CommandHandler("advisor",          advisor_command))
    app.add_handler(CommandHandler("goals",            goals_command))
    app.add_handler(CommandHandler("cancelgoal",       cancelgoal_command))
    app.add_handler(CommandHandler("plans",            plans_command))
    app.add_handler(CommandHandler("cancelplan",       cancelplan_command))
    app.add_handler(MessageHandler(filters.PHOTO,        handle_photo))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run recurring check every day at 8 AM
    app.job_queue.run_daily(
        process_recurring,
        time=datetime.time(hour=8, minute=0, tzinfo=datetime.timezone.utc),
    )

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
