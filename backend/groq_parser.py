import json
import os
import re
from datetime import datetime, timezone, timedelta

import pytz
from dotenv import load_dotenv
from groq import Groq

from categories import CATEGORY_NAMES, fuzzy_match_category

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def safe_json_parse(text: str) -> dict:
    text = re.sub(r"```json|```", "", text or "").strip()
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No valid JSON found in: {text}")


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

    # "15th May", "May 15", "15 May" with optional year
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

    # Plain month name: "May month", "in March", etc.
    for name, month_num in _MONTH_MAP.items():
        if re.search(rf"\b{name}\b", lower):
            year = today.year if month_num <= today.month else today.year - 1
            return f"{year}-{month_num:02d}-01"

    return None


def _extract_amount(message: str) -> float | None:
    matches = re.findall(r"(?<![\w.])(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.\d+)?)", message, flags=re.IGNORECASE)
    if not matches:
        return None
    try:
        return float(matches[-1].replace(",", ""))
    except ValueError:
        return None


def _compact_description(message: str) -> str:
    cleaned = re.sub(r"(?<![\w.])(?:₹|rs\.?|inr)?\s*[0-9][0-9,]*(?:\.\d+)?", "", message, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned.replace(":-", " ").replace("=", " ")).strip(" -:")
    words = cleaned.split()
    return " ".join(words[:8]) if words else "Transaction"


def _fallback_extract(message: str) -> dict:
    amount = _extract_amount(message)
    lower = message.lower()
    if amount is None:
        return {"amount": None, "type": None, "category": None, "subcategory": None, "description": _compact_description(message), "source": None, "date": _extract_date(message)}

    transaction_type = "income" if re.search(r"\b(receive|received|got|salary|income|credited)\b", lower) else "expense"

    if transaction_type == "income" and "salary" in lower:
        category = "Salary & Income"
        subcategory = None
    elif "hunger box" in lower or any(word in lower for word in ["zomato", "swiggy", "lunch", "dinner", "breakfast", "food"]):
        category = "Food & Dining"
        subcategory = "Delivery" if any(word in lower for word in ["hunger box", "zomato", "swiggy"]) else "Dining Out"
    elif any(word in lower for word in ["fish", "grocery", "groceries", "vegetable", "fruit", "milk"]):
        category = "Groceries"
        subcategory = "Dairy" if "milk" in lower else "Fruits" if "fruit" in lower else "Vegetables"
    elif any(word in lower for word in ["bikewash", "bike wash", "petrol", "diesel", "auto", "uber", "ola", "fuel"]):
        category = "Transport"
        subcategory = "Fuel" if any(word in lower for word in ["petrol", "diesel", "fuel"]) else "Auto" if "auto" in lower else "Cab" if any(word in lower for word in ["uber", "ola"]) else None
    elif any(word in lower for word in ["dress", "dresses", "makeup", "kit", "amazon", "flipkart", "myntra", "shopping"]):
        category = "Shopping"
        subcategory = "Beauty" if "makeup" in lower else "Clothes" if any(word in lower for word in ["dress", "dresses"]) else None
    elif transaction_type == "income":
        category = "Gifts & Misc"
        subcategory = None
    else:
        category = "Gifts & Misc"
        subcategory = "Home Decor" if "flower pot" in lower else None

    source = None
    from_match = re.search(r"\bfrom\s+([A-Z][A-Za-z]+)", message)
    spend_match = re.search(r"\bspend\s+([A-Z][A-Za-z]+)\b", message)
    if from_match:
        source = from_match.group(1)
    elif spend_match:
        source = spend_match.group(1)
    elif "hunger box" in lower:
        source = "Hunger Box"

    return {
        "amount": amount,
        "type": transaction_type,
        "category": category,
        "subcategory": subcategory,
        "description": _compact_description(message),
        "source": source,
        "date": _extract_date(message),
    }


def _normalize_result(parsed: dict, message: str) -> dict:
    fallback = _fallback_extract(message)
    lower = message.lower()
    if parsed.get("amount") is None and fallback.get("amount") is not None:
        parsed = fallback

    if parsed.get("amount") is not None:
        try:
            parsed["amount"] = float(str(parsed["amount"]).replace(",", ""))
        except (TypeError, ValueError):
            parsed["amount"] = fallback.get("amount")

    trust_fallback = any(
        phrase in lower
        for phrase in [
            "flower pot",
            "fish",
            "bikewash",
            "bike wash",
            "petrol",
            "auto",
            "hunger box",
            "makeup",
            "dress",
            "dresses",
        ]
    ) or (re.search(r"\b(receive|received|got|credited)\b", lower) and "salary" not in lower)

    if trust_fallback and fallback.get("amount") is not None:
        parsed["type"] = fallback.get("type")
        parsed["category"] = fallback.get("category")
        parsed["subcategory"] = fallback.get("subcategory") or parsed.get("subcategory")
        parsed["source"] = fallback.get("source") or parsed.get("source")
    else:
        parsed["type"] = parsed.get("type") if parsed.get("type") in {"expense", "income", None} else fallback.get("type")
        llm_cat = parsed.get("category")
        if llm_cat:
            # Fuzzy-map to a known category if the LLM returned a close variant (e.g. "Health" → "Health & Medical")
            # Keep the original if it's genuinely new (e.g. "Pet Care", "Electronics")
            parsed["category"] = fuzzy_match_category(llm_cat) or llm_cat
        else:
            parsed["category"] = fallback.get("category")

    parsed["description"] = " ".join(str(parsed.get("description") or fallback.get("description") or "Transaction").split()[:8])
    parsed["subcategory"] = parsed.get("subcategory") or fallback.get("subcategory")
    parsed["source"] = parsed.get("source") or fallback.get("source")
    # Regex extraction is authoritative for relative dates (yesterday, last month, in May) because the
    # LLM doesn't know the actual current date and can't resolve them reliably.
    # Fall back to LLM's literal date only when the regex finds nothing (e.g. "15/06/2026 petrol 500").
    date = _extract_date(message) or parsed.get("date") or fallback.get("date")
    return {
        "amount": parsed.get("amount"),
        "type": parsed.get("type"),
        "category": parsed.get("category"),
        "subcategory": parsed.get("subcategory"),
        "description": parsed.get("description"),
        "source": parsed.get("source"),
        "date": date,
    }


def extract_from_text(user_message: str) -> dict:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not configured.")
    if not user_message or not user_message.strip():
        raise ValueError("Message is empty.")

    system_prompt = """You are a smart finance assistant for an Indian user.
Your job is to extract transaction details from casual, informal messages in English or Hindi-English mix.

RULES:
- Amount can appear ANYWHERE in the message (before or after description)
- Amounts may have commas like 10,000 — treat as 10000
- Amounts may have :- or = before them like "Salary :- 24500"
- "receive", "received", "got", "salary", "income", "credited" = income
- Everything else = expense
- Casual phrases like "i spend X on Y", "i bought X", "i buy X" are valid expenses
- Person names (Sanket, Hridu) = source field, not category
- "hunger box" = food delivery app = Food & Dining category
- "bikewash" = Transport category
- If the message has NO amount at all (like "hi", "hello", "how are you") → return amount as null
- For date: extract ONLY if explicitly mentioned (yesterday, today, May 15, last month, in March, etc.)
  Format as YYYY-MM-DD. Use current year unless a different year is stated.
  If no date is mentioned → return null.

Return ONLY a single raw JSON object, nothing else, no explanation, no extra text:
{
  "amount": <float or null>,
  "type": <"expense" or "income" or null>,
  "category": <best-matching category — use a preferred category when it fits, or invent a short new name (2-4 words, Title Case) when none fit>,
  "subcategory": <more specific label or null>,
  "description": <max 8 words>,
  "source": <name of app/shop/person or null>,
  "date": <"YYYY-MM-DD" or null>
}

Subcategory examples:
Food & Dining → Delivery, Dining Out, Snacks, Beverages
Groceries → Vegetables, Dairy, Household, Fruits
Transport → Fuel, Cab, Auto, Public Transport, Parking
Shopping → Clothes, Electronics, Home Decor, Beauty, Accessories
Health & Medical → Medicine, Doctor Visit, Lab Test, Insurance
Entertainment → OTT, Movies, Events, Games
Utilities & Bills → Electricity, Internet, Gas, Water
Investment & SIP → Mutual Fund, Stocks, Gold, FD, PPF
EMI & Loans → Home Loan, Personal Loan, Credit Card, Vehicle Loan

Preferred categories (use these when they match):
"Food & Dining", "Groceries", "Transport", "Rent & Housing",
"Health & Medical", "Entertainment", "Shopping", "Subscriptions",
"Education", "EMI & Loans", "Investment & SIP", "Salary & Income",
"Gifts & Misc", "Utilities & Bills"
If none of the above fit, create a short descriptive category name (2-4 words, Title Case, e.g. "Pet Care", "Electronics", "Travel").

IMPORTANT: Return ONLY the JSON object. No markdown. No explanation. No extra lines. Just one JSON."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        return _normalize_result(safe_json_parse(text), user_message)
    except Exception as exc:
        fallback = _fallback_extract(user_message)
        if fallback.get("amount") is not None:
            return fallback
        raise RuntimeError(f"Groq extraction failed: {exc}") from exc
