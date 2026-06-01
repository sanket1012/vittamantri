import os
import logging
import pathlib
from functools import wraps
from io import StringIO

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from data_manager import (
    bulk_update_transactions,
    clean_garbage,
    delete_transaction,
    export_monthly_report,
    get_all_transactions,
    get_all_users,
    get_categories,
    get_categories_with_subcategories,
    get_summary,
    get_transactions_by_month,
    get_transactions_by_user,
    get_user_summary,
    rebuild_summary,
    save_custom_category,
    save_custom_subcategory,
    save_transaction,
    transaction_csv_path,
    update_transaction_fields,
)
from gemini_parser import extract_from_image, extract_from_pdf
from groq_parser import extract_from_text

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vittamantri.api")

_DEBUG = os.getenv("DEBUG", "false").lower() == "true"
_DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "")
_DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "")
_DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
_STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "dist"

_ALLOWED_ORIGINS = [os.getenv("FRONTEND_URL", "http://localhost:5173")]
if _DEBUG:
    _ALLOWED_ORIGINS += ["http://localhost:5173", "http://localhost:3000"]

app = Flask(__name__)
CORS(app, origins=_ALLOWED_ORIGINS, allow_headers=["Content-Type", "X-Api-Key"], supports_credentials=False)

_MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB
_MAX_PDF_BYTES = 20 * 1024 * 1024     # 20 MB
_ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_ALLOWED_IMAGE_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",
    b"GIF8": "image/gif",
}


def _internal_error():
    return jsonify({"error": "Internal server error"}), 500


def error_response(message: str, status: int = 400):
    return jsonify({"error": message}), status


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _DASHBOARD_API_KEY:
            logger.warning("DASHBOARD_API_KEY is not set — API is unprotected")
            return f(*args, **kwargs)
        if request.headers.get("X-Api-Key") != _DASHBOARD_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def _validate_image_file(file):
    """Returns (bytes, mime_type) or raises ValueError."""
    raw = file.read(_MAX_IMAGE_BYTES + 1)
    if len(raw) > _MAX_IMAGE_BYTES:
        raise ValueError("File exceeds 10 MB limit.")
    for magic, mime in _ALLOWED_IMAGE_MAGIC.items():
        if raw[:len(magic)] == magic:
            return raw, mime
    raise ValueError("Unsupported image format. Use JPEG, PNG, WebP, or GIF.")


def _validate_pdf_file(file):
    """Returns bytes or raises ValueError."""
    raw = file.read(_MAX_PDF_BYTES + 1)
    if len(raw) > _MAX_PDF_BYTES:
        raise ValueError("File exceeds 20 MB limit.")
    if not raw.startswith(b"%PDF"):
        raise ValueError("File does not appear to be a valid PDF.")
    return raw


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health_check():
    return jsonify({"status": "वित्तमंत्री is running"})


@app.route("/api/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")
    if not _DASHBOARD_USERNAME or not _DASHBOARD_PASSWORD:
        return error_response("Login not configured on server.", 500)
    if username == _DASHBOARD_USERNAME and password == _DASHBOARD_PASSWORD:
        return jsonify({"token": _DASHBOARD_API_KEY})
    return jsonify({"error": "Invalid username or password"}), 401


# ── Transactions ──────────────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
@require_api_key
def list_transactions():
    try:
        month_filter = request.args.get("month")
        transactions = get_all_transactions()
        if month_filter:
            transactions = [t for t in transactions if str(t.get("date", "")).startswith(month_filter)]
        return jsonify({"transactions": transactions})
    except Exception:
        logger.exception("list_transactions failed")
        return _internal_error()


@app.route("/api/transactions/<id>", methods=["GET"])
@require_api_key
def get_transaction(id):
    try:
        transaction = next((t for t in get_all_transactions() if t.get("id") == id), None)
        if not transaction:
            return error_response("Transaction not found.", 404)
        return jsonify(transaction)
    except Exception:
        logger.exception("get_transaction failed")
        return _internal_error()


@app.route("/api/transactions", methods=["POST"])
@require_api_key
def add_transaction():
    try:
        payload = request.get_json(silent=True) or {}
        transaction_id = save_transaction(payload)
        transaction = next((t for t in get_all_transactions() if t.get("id") == transaction_id), None)
        return jsonify({"id": transaction_id, "transaction": transaction, "message": "Transaction saved."}), 201
    except Exception:
        logger.exception("add_transaction failed")
        return _internal_error()


@app.route("/api/transactions/batch", methods=["PATCH"])
@require_api_key
def batch_patch_transactions():
    try:
        payload = request.get_json(silent=True) or {}
        ids = payload.get("ids", [])
        fields = payload.get("fields", {})
        if not ids:
            return error_response("ids is required.", 400)
        if not fields:
            return error_response("fields is required.", 400)
        count = bulk_update_transactions(ids, fields)
        return jsonify({"updated_count": count, "message": f"Updated {count} transactions."})
    except Exception:
        logger.exception("batch_patch_transactions failed")
        return _internal_error()


@app.route("/api/transactions/<id>", methods=["PATCH"])
@require_api_key
def patch_transaction(id):
    try:
        payload = request.get_json(silent=True) or {}
        mutable = {"category", "subcategory", "description", "source", "type", "amount", "date"}
        fields = {k: v for k, v in payload.items() if k in mutable and v is not None}
        if not fields:
            return error_response("At least one editable field is required.", 400)
        if not update_transaction_fields(id, fields):
            return error_response("Transaction not found.", 404)
        transaction = next((t for t in get_all_transactions() if t.get("id") == id), None)
        return jsonify({"id": id, "transaction": transaction, "message": "Transaction updated."})
    except Exception:
        logger.exception("patch_transaction failed")
        return _internal_error()


@app.route("/api/transactions/<id>", methods=["DELETE"])
@require_api_key
def remove_transaction(id):
    try:
        if not delete_transaction(id):
            return jsonify({"success": False, "message": "Transaction not found"}), 404
        return jsonify({"success": True, "message": "Transaction deleted"})
    except Exception:
        logger.exception("remove_transaction failed")
        return _internal_error()


@app.route("/api/transactions/clean", methods=["DELETE"])
@require_api_key
def clean_transactions():
    try:
        deleted_count = clean_garbage()
        return jsonify({"deleted_count": deleted_count, "message": f"Removed {deleted_count} garbage transactions"})
    except Exception:
        logger.exception("clean_transactions failed")
        return _internal_error()


# ── Summary ───────────────────────────────────────────────────────────────────

@app.route("/api/summary", methods=["GET"])
@require_api_key
def summary():
    try:
        return jsonify(rebuild_summary())
    except Exception:
        logger.exception("summary failed")
        return _internal_error()


@app.route("/api/categories", methods=["GET"])
@require_api_key
def categories():
    try:
        return jsonify(get_categories())
    except Exception:
        logger.exception("categories failed")
        return _internal_error()


@app.route("/api/users", methods=["GET"])
@require_api_key
def users():
    try:
        return jsonify(get_all_users())
    except Exception:
        logger.exception("users failed")
        return _internal_error()


@app.route("/api/transactions/user/<int:logged_by_id>", methods=["GET"])
@require_api_key
def transactions_by_user(logged_by_id):
    try:
        return jsonify({"transactions": get_transactions_by_user(logged_by_id)})
    except Exception:
        logger.exception("transactions_by_user failed")
        return _internal_error()


@app.route("/api/summary/user/<int:logged_by_id>", methods=["GET"])
@require_api_key
def summary_by_user(logged_by_id):
    try:
        return jsonify(get_user_summary(logged_by_id))
    except Exception:
        logger.exception("summary_by_user failed")
        return _internal_error()


@app.route("/api/summary/monthly", methods=["GET"])
@require_api_key
def monthly_summary():
    try:
        return jsonify(get_summary().get("monthly_totals", {}))
    except Exception:
        logger.exception("monthly_summary failed")
        return _internal_error()


@app.route("/api/summary/categories", methods=["GET"])
@require_api_key
def category_summary():
    try:
        return jsonify(get_summary().get("category_totals", {}))
    except Exception:
        logger.exception("category_summary failed")
        return _internal_error()


# ── Export ────────────────────────────────────────────────────────────────────

@app.route("/api/export/csv", methods=["GET"])
@require_api_key
def export_csv():
    try:
        return send_file(transaction_csv_path(), as_attachment=True, download_name="transactions.csv", mimetype="text/csv")
    except Exception:
        logger.exception("export_csv failed")
        return _internal_error()


@app.route("/api/export/monthly/<int:year>/<int:month>", methods=["GET"])
@require_api_key
def export_monthly(year, month):
    try:
        if not (1 <= month <= 12):
            return error_response("Month must be between 1 and 12.", 400)
        if not (2000 <= year <= 2100):
            return error_response("Year must be between 2000 and 2100.", 400)
        csv_text = export_monthly_report(year, month)
        return Response(
            csv_text,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=vittamantri-{year}-{month:02d}.csv"},
        )
    except Exception:
        logger.exception("export_monthly failed")
        return _internal_error()


# ── Parse ─────────────────────────────────────────────────────────────────────

@app.route("/api/parse/text", methods=["POST"])
@require_api_key
def parse_text():
    try:
        payload = request.get_json(silent=True) or {}
        message = payload.get("message", "")
        if not message:
            return error_response("message is required.", 400)
        extracted = extract_from_text(message)
        return jsonify({"transaction": extracted})
    except Exception:
        logger.exception("parse_text failed")
        return _internal_error()


@app.route("/api/parse/image", methods=["POST"])
@require_api_key
def parse_image():
    try:
        file = request.files.get("image") or request.files.get("file")
        if not file:
            return error_response("image file is required.", 400)
        image_bytes, mime_type = _validate_image_file(file)
        transactions = extract_from_image(image_bytes, mime_type)
        return jsonify({"transactions": transactions})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        logger.exception("parse_image failed")
        return _internal_error()


@app.route("/api/parse/pdf", methods=["POST"])
@require_api_key
def parse_pdf():
    try:
        file = request.files.get("pdf") or request.files.get("file")
        if not file:
            return error_response("pdf file is required.", 400)
        pdf_bytes = _validate_pdf_file(file)
        transactions = extract_from_pdf(pdf_bytes)
        return jsonify({"transactions": transactions})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        logger.exception("parse_pdf failed")
        return _internal_error()


# ── React frontend (production) ───────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if not _STATIC_DIR.exists():
        return jsonify({"error": "Frontend not built"}), 404
    target = _STATIC_DIR / path
    if path and target.exists() and target.is_file():
        return send_from_directory(_STATIC_DIR, path)
    return send_from_directory(_STATIC_DIR, "index.html")


if __name__ == "__main__":
    app.run(debug=_DEBUG, port=8000, use_reloader=False)
