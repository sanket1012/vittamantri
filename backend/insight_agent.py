"""LLM-backed Q&A and narrative insight generation, scoped to the current
month's household transactions. Shared by the web app's chat UI and the
Telegram bot's open-ended question fallback."""

import json
import logging
from datetime import datetime

import pytz

from data_manager import get_transactions_by_month
from groq_parser import GroqUnavailableError, client as groq_client

logger = logging.getLogger("vittamantri.insight_agent")

_IST = pytz.timezone("Asia/Kolkata")
_MODEL = "openai/gpt-oss-120b"
_MAX_TRANSACTIONS_IN_CONTEXT = 300
_MAX_HISTORY_TURNS = 6


def _current_month():
    now = datetime.now(_IST)
    return now.year, now.month, now.strftime("%B %Y")


def _build_month_context(household_id: int) -> dict:
    year, month, label = _current_month()
    rows = get_transactions_by_month(year, month, household_id)[:_MAX_TRANSACTIONS_IN_CONTEXT]

    total_income = sum(r["amount"] for r in rows if r["type"] == "income")
    total_expense = sum(r["amount"] for r in rows if r["type"] == "expense")

    by_category: dict[str, float] = {}
    for r in rows:
        if r["type"] == "expense":
            key = r["category"] or "Uncategorized"
            by_category[key] = by_category.get(key, 0) + r["amount"]

    return {
        "month_label": label,
        "summary": {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_savings": round(total_income - total_expense, 2),
            "transaction_count": len(rows),
        },
        "category_totals": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda kv: -kv[1])},
        "transactions": [
            {
                "date": r["date"],
                "amount": r["amount"],
                "type": r["type"],
                "category": r["category"],
                "subcategory": r["subcategory"],
                "description": r["description"],
                "source": r["source"],
                "logged_by": r["logged_by"],
            }
            for r in rows
        ],
    }


_SYSTEM_PROMPT_TEMPLATE = """You are Samvitta's financial assistant for an Indian household, speaking plainly and warmly.
Answer using ONLY the transaction data for {month_label} given below as JSON — never invent numbers,
and never answer questions about other months since you don't have that data; say so instead.
Amounts are in INR (₹). Keep answers concise — a few sentences, not an essay. Format amounts like ₹1,234.

DATA FOR {month_label}:
{data_json}"""


def _call_groq(system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    for turn in (history or [])[-_MAX_HISTORY_TURNS:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": str(turn["content"])[:2000]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = groq_client.chat.completions.create(model=_MODEL, messages=messages, temperature=0.3, max_tokens=500)
        return response.choices[0].message.content
    except Exception as exc:
        logger.warning("Insight agent Groq call failed: %s", exc)
        raise GroqUnavailableError(str(exc)) from exc


def ask(household_id: int, question: str, history: list[dict] | None = None) -> str:
    """Answers a free-text question about the current month's household finances."""
    context = _build_month_context(household_id)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        month_label=context["month_label"], data_json=json.dumps(context, ensure_ascii=False)
    )
    return _call_groq(system_prompt, question, history)


def generate_monthly_insight(household_id: int) -> str:
    """Generates an on-demand narrative summary of the current month's finances."""
    context = _build_month_context(household_id)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        month_label=context["month_label"], data_json=json.dumps(context, ensure_ascii=False)
    )
    prompt = (
        f"Write a short narrative summary (3-5 sentences) of this household's {context['month_label']} finances: "
        "how much they earned/spent, their top spending categories, anything notable (a big single transaction, "
        "an unusual category), and one practical, specific observation. Avoid generic advice."
    )
    return _call_groq(system_prompt, prompt)
