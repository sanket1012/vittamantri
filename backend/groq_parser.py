import json
import logging
import os
import re
from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv
from groq import Groq

from categories import build_categories_prompt_str, fuzzy_match_category

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
logger = logging.getLogger("vittamantri.groq")

_IST = pytz.timezone("Asia/Kolkata")

_MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _today_ist() -> datetime:
    return datetime.now(_IST)


def _extract_date(message: str) -> str | None:
    """Regex-based date extraction as a safety override for relative date phrases.

    The LLM knows today's date and handles most cases, but regex is more reliable
    for "yesterday", "last month", "May 15" patterns.
    """
    lower = message.lower()
    today = _today_ist()

    if "last month" in lower or "previous month" in lower:
        first = today.replace(day=1)
        last_month = (first - timedelta(days=1)).replace(day=1)
        return last_month.strftime("%Y-%m-%d")

    if "yesterday" in lower:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    if "today" in lower:
        return today.strftime("%Y-%m-%d")

    day_month = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(_MONTH_MAP) + r")\b",
        lower,
    )
    month_day = re.search(
        r"\b(" + "|".join(_MONTH_MAP) + r")\s+(\d{1,2})(?:st|nd|rd|th)?\b",
        lower,
    )
    match = day_month or month_day
    if match:
        if day_month:
            day, month_name = int(match.group(1)), match.group(2)
        else:
            month_name, day = match.group(1), int(match.group(2))
        month_num = _MONTH_MAP[month_name]
        year = today.year if month_num <= today.month else today.year - 1
        try:
            return datetime(year, month_num, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Plain month name: "May month", "in March"
    for name, month_num in _MONTH_MAP.items():
        if re.search(rf"\b{name}\b", lower):
            year = today.year if month_num <= today.month else today.year - 1
            return f"{year}-{month_num:02d}-01"

    return None


def _parse_response(raw: str) -> dict:
    """Parse LLM response into a dict. Returns {} on any parse failure."""
    text = re.sub(r"```json|```", "", raw or "").strip()
    # Try direct parse first (clean JSON output)
    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else {}
    except json.JSONDecodeError:
        pass
    # Extract from first { to last } (handles explanation text around the JSON)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse LLM response as JSON: %r", raw[:200])
    return {}


def _process_transaction(txn: dict, message: str, all_category_names: list[str]) -> dict | None:
    """Normalise a single transaction dict returned by the LLM. Returns None if no valid amount."""
    amount = txn.get("amount")
    if amount is not None:
        try:
            amount = float(str(amount).replace(",", ""))
        except (TypeError, ValueError):
            amount = None
    if not amount:
        return None

    category = txn.get("category") or ""
    if category:
        category = fuzzy_match_category(category, extra_names=all_category_names) or category

    # Regex date is authoritative for relative phrases; fall back to LLM's value
    date = _extract_date(message) or txn.get("date")

    return {
        "amount": amount,
        "type": txn.get("type"),
        "category": category or None,
        "subcategory": txn.get("subcategory"),
        "description": " ".join(str(txn.get("description") or "Transaction").split()[:8]),
        "source": txn.get("source"),
        "date": date,
        "confidence": txn.get("confidence"),
    }


def extract_from_text(user_message: str, all_categories: list[dict] | None = None) -> dict:
    """Extract transactions from a free-text message using the LLM.

    Returns {"query": str|None, "transactions": [...]}.
    transactions is an empty list if nothing was extracted or the message is a query/greeting.
    """
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not configured.")
    if not user_message or not user_message.strip():
        raise ValueError("Message is empty.")

    all_category_names: list[str] = [c["name"] for c in (all_categories or [])]
    today = _today_ist().strftime("%Y-%m-%d")

    if all_categories:
        cats_str = build_categories_prompt_str(all_categories)
        category_instructions = (
            f"Existing categories and subcategories: {cats_str}\n"
            "Reuse an existing category/subcategory when it fits; "
            "create a new one (2-4 words, Title Case) only when nothing matches."
        )
    else:
        category_instructions = (
            'Preferred categories: "Food & Dining", "Groceries", "Transport", "Rent & Housing", '
            '"Health & Medical", "Entertainment", "Shopping", "Subscriptions", "Education", '
            '"EMI & Loans", "Investment & SIP", "Salary & Income", "Gifts & Misc", "Utilities & Bills". '
            "If none fit, create a short descriptive name (2-4 words, Title Case)."
        )

    system_prompt = f"""You are a personal finance assistant for an Indian user on Telegram.
Classify the message and extract all transactions. Today is {today}.

MESSAGE TYPES:
1. Transaction log — recording money spent or received. May contain multiple transactions.
2. Finance query — asking about their data (balance, today, this week, this month).
3. Greeting — hi, hello, thanks, ok, etc.

RULES for transactions:
- A single message may contain multiple transactions separated by commas or newlines — extract ALL of them
- Amount can appear ANYWHERE (before or after description)
- Amounts may have commas (10,000 → 10000) or prefixes like :- or =
- Month names ("May month", "last month") describe WHEN, not what — still extract the amount
- "receive", "received", "got", "salary", "income", "credited" → type: income; everything else → expense
- Person names = source field, not category
- date: YYYY-MM-DD if a date/month is mentioned, else null
- confidence: "high" if amount+category clear; "medium" if inferred; "low" only if truly no number

{category_instructions}

Return ONLY a raw JSON object:
{{
  "query": <null if logging transactions, or "today" | "week" | "month" | "balance" | "greeting">,
  "transactions": [
    {{
      "amount": <positive float or null>,
      "type": <"expense" or "income">,
      "category": <existing or new category name>,
      "subcategory": <subcategory or null>,
      "description": <max 8 words>,
      "source": <app/shop/person or null>,
      "date": <"YYYY-MM-DD" or null>,
      "confidence": <"high" or "medium" or "low">
    }}
  ]
}}

Examples:
- "Zomato 280" → query: null, transactions: [{{amount:280, category:"Food & Dining", ...}}]
- "Zomato 280, petrol 500" → query: null, transactions: [{{amount:280,...}}, {{amount:500,...}}]
- "May month Home EMI 65000" → query: null, transactions: [{{amount:65000, category:"EMI & Loans",...}}]
- "my balance" → query: "balance", transactions: []
- "hi" → query: "greeting", transactions: []"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=600,
        )
        raw = response.choices[0].message.content
        logger.info("LLM raw response for %r: %s", user_message[:60], raw)
        parsed = _parse_response(raw)
        logger.info("LLM parsed result: %s", parsed)
    except Exception as exc:
        logger.warning("Groq API call failed for %r: %s", user_message[:60], exc)
        return {"query": None, "transactions": []}

    if not parsed:
        return {"query": None, "transactions": []}

    query = parsed.get("query") if parsed.get("query") in ("today", "week", "month", "balance", "greeting") else None
    raw_transactions = parsed.get("transactions") or []

    transactions = [
        t for t in (
            _process_transaction(txn, user_message, all_category_names)
            for txn in raw_transactions
            if isinstance(txn, dict)
        )
        if t is not None
    ]

    return {"query": query, "transactions": transactions}
