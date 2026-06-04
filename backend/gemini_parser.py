import json
import logging
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

from categories import build_categories_prompt_str, CATEGORY_NAMES, SUBCATEGORY_MAP, fuzzy_match_category

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
logger = logging.getLogger("vittamantri.gemini")

_DEFAULT_CATS = build_categories_prompt_str([
    {"name": name, "subcategories": SUBCATEGORY_MAP.get(name, [])}
    for name in CATEGORY_NAMES
])


def _parse_json_array(raw: str) -> list:
    """Robustly extract a JSON array from the LLM response."""
    text = re.sub(r"```json|```", "", raw or "").strip()
    # Try direct parse first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        # Gemini sometimes wraps in {"transactions": [...]}
        if isinstance(result, dict):
            for v in result.values():
                if isinstance(v, list):
                    return v
    except json.JSONDecodeError:
        pass
    # Extract from first [ to last ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse Gemini response as JSON array: %r", raw[:200])
    return []


def _require_key() -> None:
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not configured.")


def _cats_str(all_categories: list[dict] | None) -> str:
    if all_categories:
        return build_categories_prompt_str(all_categories)
    return _DEFAULT_CATS


def _normalise_transactions(raw_list: list, all_categories: list[dict] | None) -> list:
    """Coerce amounts and fuzzy-map categories for each item in the list."""
    all_cat_names = [c["name"] for c in (all_categories or [])]
    result = []
    for txn in raw_list:
        if not isinstance(txn, dict):
            continue
        amount = txn.get("amount")
        try:
            amount = float(str(amount).replace(",", "")) if amount is not None else None
        except (TypeError, ValueError):
            amount = None
        if not amount:
            continue
        category = txn.get("category") or ""
        if category:
            category = fuzzy_match_category(category, extra_names=all_cat_names) or category
        result.append({
            "amount": amount,
            "type": txn.get("type"),
            "category": category or None,
            "subcategory": txn.get("subcategory"),
            "description": " ".join(str(txn.get("description") or "Transaction").split()[:8]),
            "source": txn.get("source"),
            "date": txn.get("date"),
        })
    return result


def extract_from_image(image_bytes: bytes, mime_type: str = "image/jpeg", all_categories: list[dict] | None = None) -> list:
    _require_key()
    if not image_bytes:
        raise ValueError("Image upload is empty.")

    cats = _cats_str(all_categories)
    prompt = f"""You are a finance assistant analyzing an Indian receipt, bill, UPI app screenshot, PhonePe, Google Pay, or Paytm screenshot.
Extract ALL transactions visible, including successful UPI payments.
Return ONLY a valid JSON array, each object with:
- amount: (positive float in INR)
- type: ("expense" or "income")
- category: (reuse existing name when it fits, else create a short new one)
- subcategory: (specific sub-label or null)
- description: (what was purchased, max 8 words)
- source: (merchant/app/person name if visible, else null)
- date: (YYYY-MM-DD if visible, else null)

Existing categories and subcategories: {cats}
Reuse an existing category/subcategory when it fits; create a new one only when nothing matches.

Rules:
- "Paid to" / debit screens → expense; "Received from" / cashback / credited → income.
- If category is truly unclear, use "Gifts & Misc".

Return ONLY raw JSON array. No explanation. No markdown."""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        raw = response.text.strip()
        logger.info("Gemini image raw response: %s", raw[:300])
        transactions = _parse_json_array(raw)
        return _normalise_transactions(transactions, all_categories)
    except Exception as exc:
        raise RuntimeError(f"Gemini image extraction failed: {exc}") from exc


def extract_from_pdf(pdf_bytes: bytes, all_categories: list[dict] | None = None) -> list:
    _require_key()
    if not pdf_bytes:
        raise ValueError("PDF upload is empty.")

    cats = _cats_str(all_categories)
    prompt = f"""You are a finance assistant analyzing an Indian bank statement or PDF bill.
Extract ALL transactions you can find.
Return ONLY a valid JSON array, each object with:
- amount: (positive float in INR)
- type: ("expense" or "income")
- category: (reuse existing name when it fits, else create a short new one)
- subcategory: (specific sub-label or null)
- description: (what the transaction was, max 8 words)
- source: (merchant/bank name if visible, else null)
- date: (YYYY-MM-DD if visible, else null)

Existing categories and subcategories: {cats}
Reuse an existing category/subcategory when it fits; create a new one only when nothing matches.

Return ONLY raw JSON array. No explanation. No markdown."""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt,
            ],
        )
        raw = response.text.strip()
        logger.info("Gemini PDF raw response: %s", raw[:300])
        transactions = _parse_json_array(raw)
        return _normalise_transactions(transactions, all_categories)
    except Exception as exc:
        raise RuntimeError(f"Gemini PDF extraction failed: {exc}") from exc
