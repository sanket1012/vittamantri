import json
import os
import re
from datetime import datetime, timezone, timedelta

import pytz
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CATEGORY_NAMES = {
    "Food & Dining",
    "Groceries",
    "Transport",
    "Rent & Housing",
    "Health & Medical",
    "Entertainment",
    "Shopping",
    "Subscriptions",
    "Education",
    "EMI & Loans",
    "Investment & SIP",
    "Salary & Income",
    "Gifts & Misc",
    "Utilities & Bills",
}


def safe_json_parse(text: str) -> dict:
    text = re.sub(r"```json|```", "", text or "").strip()
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No valid JSON found in: {text}")


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
        return {"amount": None, "type": None, "category": None, "subcategory": None, "description": _compact_description(message), "source": None}

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
        parsed["category"] = parsed.get("category") if parsed.get("category") in CATEGORY_NAMES or parsed.get("category") is None else fallback.get("category")

    parsed["description"] = " ".join(str(parsed.get("description") or fallback.get("description") or "Transaction").split()[:8])
    parsed["subcategory"] = parsed.get("subcategory") or fallback.get("subcategory")
    parsed["source"] = parsed.get("source") or fallback.get("source")
    return {
        "amount": parsed.get("amount"),
        "type": parsed.get("type"),
        "category": parsed.get("category"),
        "subcategory": parsed.get("subcategory"),
        "description": parsed.get("description"),
        "source": parsed.get("source"),
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

Return ONLY a single raw JSON object, nothing else, no explanation, no extra text:
{
  "amount": <float or null>,
  "type": <"expense" or "income" or null>,
  "category": <one of the 14 categories or null>,
  "subcategory": <more specific label or null>,
  "description": <max 8 words>,
  "source": <name of app/shop/person or null>
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

Categories: "Food & Dining", "Groceries", "Transport", "Rent & Housing",
"Health & Medical", "Entertainment", "Shopping", "Subscriptions",
"Education", "EMI & Loans", "Investment & SIP", "Salary & Income",
"Gifts & Misc", "Utilities & Bills"

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
