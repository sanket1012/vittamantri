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
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse LLM response as JSON: %r", raw[:200])
    return {}


def extract_from_text(user_message: str, all_categories: list[dict] | None = None) -> dict:
    """Extract a transaction from free text using the LLM.

    Returns a dict with transaction fields, or {} if nothing could be extracted.
    Low-confidence results are returned as-is; the caller decides whether to save them.
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

    system_prompt = f"""You are a smart finance assistant for an Indian user.
Extract transaction details from casual messages in English or Hindi-English mix.

Today is {today}. Use this to resolve relative dates like "yesterday", "last month", "May month".

RULES:
- Amount can appear ANYWHERE in the message (before or after description)
- Amounts may have commas (10,000 → 10000) or prefixes like :- or =
- "receive", "received", "got", "salary", "income", "credited" → type: income
- Everything else → type: expense
- Person names = source field, not category
- If the message has NO amount → return amount as null
- date: YYYY-MM-DD if explicitly mentioned, else null
- confidence: "high" if amount+category are clear; "medium" if inferred; "low" if very uncertain

{category_instructions}

Return ONLY a raw JSON object, no markdown, no explanation:
{{
  "amount": <positive float or null>,
  "type": <"expense" or "income" or null>,
  "category": <existing or new category name>,
  "subcategory": <existing or new subcategory, or null>,
  "description": <max 8 words>,
  "source": <app/shop/person name or null>,
  "date": <"YYYY-MM-DD" or null>,
  "confidence": <"high" or "medium" or "low">
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        parsed = _parse_response(response.choices[0].message.content)
    except Exception as exc:
        logger.warning("Groq API call failed for %r: %s", user_message[:60], exc)
        return {}

    if not parsed:
        return {}

    # Coerce amount to float
    amount = parsed.get("amount")
    if amount is not None:
        try:
            amount = float(str(amount).replace(",", ""))
        except (TypeError, ValueError):
            amount = None

    # Fuzzy-map category to closest known/custom name; keep as-is if genuinely new
    category = parsed.get("category") or ""
    if category:
        category = fuzzy_match_category(category, extra_names=all_category_names) or category

    # Regex date override is more reliable than LLM for relative phrases
    date = _extract_date(user_message) or parsed.get("date")

    return {
        "amount": amount,
        "type": parsed.get("type"),
        "category": category or None,
        "subcategory": parsed.get("subcategory"),
        "description": " ".join(str(parsed.get("description") or "Transaction").split()[:8]),
        "source": parsed.get("source"),
        "date": date,
        "confidence": parsed.get("confidence"),
    }
