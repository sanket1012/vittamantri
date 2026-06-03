import json
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

from categories import build_categories_prompt_str, CATEGORY_NAMES, SUBCATEGORY_MAP

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_DEFAULT_CATS = build_categories_prompt_str([
    {"name": name, "subcategories": SUBCATEGORY_MAP.get(name, [])}
    for name in CATEGORY_NAMES
])


def _parse_json_array(text: str) -> list:
    cleaned = re.sub(r"```json|```", "", text or "").strip()
    match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError("Gemini did not return a JSON array.")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, list):
        raise ValueError("Gemini response must be a JSON array.")
    return parsed


def _require_key() -> None:
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not configured.")


def extract_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> list:
    _require_key()
    if not image_bytes:
        raise ValueError("Image upload is empty.")

    prompt = """You are a finance assistant analyzing an Indian receipt, bill, UPI app screenshot, PhonePe screenshot, Google Pay screenshot, Paytm screenshot, or expense photo.
Extract ALL transactions you can see, including successful UPI payments.
Return ONLY a valid JSON array of transaction objects, each with:
- amount: (float in INR)
- type: ("expense" or "income")
- category: (one of: "Food & Dining", "Groceries", "Transport", "Rent & Housing", "Health & Medical", "Entertainment", "Shopping", "Subscriptions", "Education", "EMI & Loans", "Investment & SIP", "Salary & Income", "Gifts & Misc", "Utilities & Bills")
- description: (what was purchased or paid for, max 8 words)
- source: (shop/person/app/merchant name if visible, else null)

Rules:
- PhonePe/UPI "Paid to" or debit screens are expenses.
- "Received from", cashback, refund, or credited screens are income.
- If the merchant/person is visible, put it in source.
- If category is unclear, use "Gifts & Misc".

Return ONLY raw JSON array. No explanation. No markdown."""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        return _parse_json_array(response.text.strip())
    except Exception as exc:
        raise RuntimeError(f"Gemini image extraction failed: {exc}") from exc


def extract_from_pdf(pdf_bytes: bytes) -> list:
    _require_key()
    if not pdf_bytes:
        raise ValueError("PDF upload is empty.")

    prompt = """You are a finance assistant analyzing an Indian bank statement or PDF bill.
Extract ALL transactions you can find.
Return ONLY a valid JSON array of transaction objects, each with:
- amount: (float in INR)
- type: ("expense" or "income")
- category: (one of: "Food & Dining", "Groceries", "Transport", "Rent & Housing", "Health & Medical", "Entertainment", "Shopping", "Subscriptions", "Education", "EMI & Loans", "Investment & SIP", "Salary & Income", "Gifts & Misc", "Utilities & Bills")
- description: (what the transaction was, max 8 words)
- source: (merchant/bank name if visible, else null)
- date: (YYYY-MM-DD if visible, else null)

Return ONLY raw JSON array. No explanation. No markdown."""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt,
            ],
        )
        return _parse_json_array(response.text.strip())
    except Exception as exc:
        raise RuntimeError(f"Gemini PDF extraction failed: {exc}") from exc
