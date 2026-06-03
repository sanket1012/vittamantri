import json
import io
import time
import logging

import fitz  # PyMuPDF
import PIL.Image
from google import genai
from google.genai.errors import ServerError
from groq import Groq

logger = logging.getLogger(__name__)

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]  # fallback order

EXTRACTION_PROMPT = """\
You are a financial data extractor. Return ONLY a valid JSON object — no markdown, no explanation.

Schema:
{{
  "transactions": [
    {{
      "date": "YYYY-MM-DD",
      "amount": <positive float>,
      "type": "income" or "expense",
      "category": "<string>",
      "description": "<string>",
      "confidence": "high" or "medium" or "low",
      "recurring": false,
      "frequency": null
    }}
  ],
  "goals": [
    {{
      "name": "<string>",
      "target_amount": <positive float>,
      "target_date": "YYYY-MM-DD" or null,
      "category": "<string>"
    }}
  ],
  "plans": [
    {{
      "name": "<string>",
      "amount": <positive float>,
      "planned_date": "YYYY-MM-DD",
      "category": "<string>",
      "notes": "<string>"
    }}
  ],
  "unrecognised": "<optional string>"
}}

Rules:
- Today is {today}. Resolve all relative dates using this.
- Existing categories: {categories}. Reuse when appropriate; create new ones freely.
- transactions: past/present financial events. If none, return [].
- goals: savings targets ("I want to save X for Y by date", "goal to accumulate X"). If none, return [].
- plans: future intended one-time expenses ("planning to buy X for Y in month", "will spend X on Y"). If none, return [].
- Amounts always positive. Determine income/expense from context.
- Recurring: set recurring=true and frequency="daily"|"weekly"|"monthly" if the message implies repetition.
- A message can contain transactions AND goals AND plans — extract all.
"""


def _build_prompt(today: str, categories: list[str]) -> str:
    cats = ", ".join(categories) if categories else "none yet"
    return EXTRACTION_PROMPT.format(today=today, categories=cats)


def _parse_response(raw: str) -> dict:
    # Strip markdown fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"transactions": []}


def extract_from_text(
    user_text: str,
    today: str,
    categories: list[str],
    groq_client: Groq,
) -> dict:
    prompt = _build_prompt(today, categories)
    response = groq_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_text},
        ],
        temperature=0.1,
        max_tokens=1024,
    )
    return _parse_response(response.choices[0].message.content)


def _gemini_generate(gemini_client: genai.Client, contents: list) -> str:
    """Try each model in VISION_MODELS with up to 2 retries before falling back."""
    for model in VISION_MODELS:
        for attempt in range(3):
            try:
                response = gemini_client.models.generate_content(
                    model=model, contents=contents
                )
                if model != VISION_MODELS[0]:
                    logger.info("Gemini fallback succeeded with %s", model)
                return response.text
            except ServerError as e:
                if e.code != 503 or attempt == 2:
                    if model == VISION_MODELS[-1]:
                        raise
                    break  # try next model
                wait = 2 ** attempt
                logger.warning("Gemini %s 503, retrying in %ss (attempt %d/3)", model, wait, attempt + 1)
                time.sleep(wait)
    raise RuntimeError("All Gemini models unavailable")


def extract_from_image_bytes(
    image_bytes: bytes,
    mime_type: str,
    today: str,
    categories: list[str],
    gemini_client: genai.Client,
    caption: str | None = None,
) -> dict:
    prompt = _build_prompt(today, categories)
    img = PIL.Image.open(io.BytesIO(image_bytes))
    user_note = f"\n\nUser's note about this image: \"{caption}\"" if caption else ""
    text = _gemini_generate(
        gemini_client,
        [prompt + f"\n\nExtract all financial transactions from this image.{user_note}", img],
    )
    return _parse_response(text)


def extract_from_pdf_bytes(
    pdf_bytes: bytes,
    today: str,
    categories: list[str],
    groq_client: Groq,
    gemini_client: genai.Client,
) -> dict:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc).strip()

    if text:
        # Text-layer PDF — use Groq
        truncated = text[:8000]
        prompt = _build_prompt(today, categories)
        response = groq_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Extract all transactions from this document:\n\n{truncated}"},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        return _parse_response(response.choices[0].message.content)
    else:
        # Scanned PDF — render first page as image and use Gemini
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("jpeg")
        return extract_from_image_bytes(img_bytes, "image/jpeg", today, categories, gemini_client, caption=None)
