import logging
import os
import pathlib
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, Response, g, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from auth import (
    create_token,
    create_user,
    find_user_by_telegram_id,
    get_user_by_id,
    get_user_by_username,
    hash_password,
    load_users,
    require_admin,
    require_auth,
    save_users,
    verify_password,
)
from data_manager import (
    bulk_update_transactions,
    clean_garbage,
    delete_category,
    delete_custom_subcategory,
    delete_transaction,
    ensure_data_files,
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
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
_STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "dist"

_ALLOWED_ORIGINS = [_FRONTEND_URL]
if _DEBUG:
    _ALLOWED_ORIGINS += ["http://localhost:5173", "http://localhost:3000"]

app = Flask(__name__)
CORS(app, origins=_ALLOWED_ORIGINS, allow_headers=["Content-Type", "Authorization", "X-Bot-Key", "X-Telegram-Id"], supports_credentials=False)

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


def _validate_image_file(file):
    raw = file.read(_MAX_IMAGE_BYTES + 1)
    if len(raw) > _MAX_IMAGE_BYTES:
        raise ValueError("File exceeds 10 MB limit.")
    for magic, mime in _ALLOWED_IMAGE_MAGIC.items():
        if raw[:len(magic)] == magic:
            return raw, mime
    raise ValueError("Unsupported image format. Use JPEG, PNG, WebP, or GIF.")


def _validate_pdf_file(file):
    raw = file.read(_MAX_PDF_BYTES + 1)
    if len(raw) > _MAX_PDF_BYTES:
        raise ValueError("File exceeds 20 MB limit.")
    if not raw.startswith(b"%PDF"):
        raise ValueError("File does not appear to be a valid PDF.")
    return raw


def _hid() -> int:
    """Household ID of the authenticated user. Falls back to 1 for legacy tokens."""
    return g.current_user.get("household_id", 1)


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health_check():
    return jsonify({"status": "वित्तमंत्री is running"})


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        return error_response("Username and password are required.", 400)
    users = load_users()
    if not users:
        return error_response("No users configured. Run migrate_users.py to set up the first admin.", 503)
    user = get_user_by_username(username)
    if not user or not verify_password(user.get("password_hash", ""), password):
        return jsonify({"error": "Invalid username or password"}), 401
    ensure_data_files(user.get("household_id", 1))
    token = create_token(user)
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user.get("display_name") or user["username"].title(),
            "role": user.get("role", "member"),
            "household_id": user.get("household_id", 1),
        },
    })


@app.route("/api/register", methods=["POST"])
def register():
    """Public endpoint — creates a new user with their own isolated household."""
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    display_name = (payload.get("display_name") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return error_response("username and password are required.", 400)
    if len(password) < 6:
        return error_response("Password must be at least 6 characters.", 400)
    if len(username) < 3:
        return error_response("Username must be at least 3 characters.", 400)

    try:
        new_user, token = create_user(username, display_name, password)
        ensure_data_files(new_user["household_id"])
        return jsonify({
            "token": token,
            "user": {
                "id": new_user["id"],
                "username": new_user["username"],
                "display_name": new_user["display_name"],
                "role": new_user["role"],
                "household_id": new_user["household_id"],
            },
        }), 201
    except ValueError as exc:
        return error_response(str(exc), 409)
    except Exception:
        logger.exception("register failed")
        return _internal_error()


@app.route("/api/me", methods=["GET"])
@require_auth
def me():
    u = g.current_user
    return jsonify({
        "id": u.get("user_id"),
        "username": u.get("username"),
        "display_name": u.get("display_name"),
        "role": u.get("role"),
        "household_id": u.get("household_id", 1),
    })


@app.route("/api/me/telegram", methods=["PATCH"])
@require_auth
def link_telegram():
    """Link or update the Telegram ID for the current user."""
    try:
        payload = request.get_json(silent=True) or {}
        telegram_id_raw = payload.get("telegram_id")
        if telegram_id_raw is None:
            return error_response("telegram_id is required.", 400)
        try:
            telegram_id = int(telegram_id_raw)
        except (TypeError, ValueError):
            return error_response("telegram_id must be a number.", 400)

        current_user_id = g.current_user.get("user_id")
        users = load_users()

        # Check no other user already linked this Telegram ID
        existing = next((u for u in users if u.get("telegram_id") == telegram_id and u["id"] != current_user_id), None)
        if existing:
            return error_response("This Telegram account is already linked to another user.", 409)

        user = next((u for u in users if u["id"] == current_user_id), None)
        if not user:
            return error_response("User not found.", 404)
        user["telegram_id"] = telegram_id
        save_users(users)
        return jsonify({"message": "Telegram account linked.", "telegram_id": telegram_id})
    except Exception:
        logger.exception("link_telegram failed")
        return _internal_error()


# ── Members (admin-only management within same household) ─────────────────────

@app.route("/api/members", methods=["GET"])
@require_admin
def list_members():
    try:
        hid = _hid()
        users = load_users()
        return jsonify([{
            "id": u["id"],
            "username": u["username"],
            "display_name": u.get("display_name") or u["username"].title(),
            "role": u.get("role", "member"),
            "telegram_id": u.get("telegram_id"),
            "created_at": u.get("created_at"),
        } for u in users if u.get("household_id", 1) == hid])
    except Exception:
        logger.exception("list_members failed")
        return _internal_error()


@app.route("/api/members", methods=["POST"])
@require_admin
def add_member():
    try:
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        display_name = (payload.get("display_name") or "").strip()
        password = payload.get("password") or ""
        role = payload.get("role", "member")

        if not username or not password:
            return error_response("username and password are required.", 400)
        if len(password) < 6:
            return error_response("Password must be at least 6 characters.", 400)
        if role not in ("admin", "member"):
            return error_response("role must be 'admin' or 'member'.", 400)

        users = load_users()
        if any(u["username"].lower() == username.lower() for u in users):
            return error_response(f"Username '{username}' is already taken.", 409)

        new_id = max((u["id"] for u in users), default=0) + 1
        hid = _hid()
        new_user = {
            "id": new_id,
            "household_id": hid,
            "username": username,
            "display_name": display_name or username.title(),
            "password_hash": hash_password(password),
            "telegram_id": None,
            "role": role,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        users.append(new_user)
        save_users(users)
        logger.info("Member created: %s (household=%d, role=%s)", username, hid, role)
        return jsonify({
            "id": new_id,
            "username": username,
            "display_name": new_user["display_name"],
            "role": role,
            "message": f"Member '{username}' created.",
        }), 201
    except Exception:
        logger.exception("add_member failed")
        return _internal_error()


@app.route("/api/members/<int:member_id>", methods=["DELETE"])
@require_admin
def delete_member(member_id):
    try:
        if member_id == g.current_user.get("user_id"):
            return error_response("Cannot delete your own account.", 400)
        hid = _hid()
        users = load_users()
        target = next((u for u in users if u["id"] == member_id), None)
        if not target:
            return error_response("Member not found.", 404)
        if target.get("household_id", 1) != hid:
            return error_response("Cannot delete a member from another household.", 403)
        new_users = [u for u in users if u["id"] != member_id]
        save_users(new_users)
        logger.info("Member %d deleted by %s", member_id, g.current_user.get("username"))
        return jsonify({"message": "Member deleted."})
    except Exception:
        logger.exception("delete_member failed")
        return _internal_error()


@app.route("/api/members/<int:member_id>/password", methods=["PATCH"])
@require_auth
def update_member_password(member_id):
    try:
        current = g.current_user
        if current.get("role") != "admin" and current.get("user_id") != member_id:
            return jsonify({"error": "Forbidden"}), 403

        payload = request.get_json(silent=True) or {}
        new_password = payload.get("password") or ""
        if len(new_password) < 6:
            return error_response("Password must be at least 6 characters.", 400)

        users = load_users()
        user = next((u for u in users if u["id"] == member_id), None)
        if not user:
            return error_response("Member not found.", 404)

        user["password_hash"] = hash_password(new_password)
        save_users(users)
        return jsonify({"message": "Password updated."})
    except Exception:
        logger.exception("update_member_password failed")
        return _internal_error()


# ── Transactions ──────────────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
@require_auth
def list_transactions():
    try:
        hid = _hid()
        month_filter = request.args.get("month")
        transactions = get_all_transactions(hid)
        if month_filter:
            transactions = [t for t in transactions if str(t.get("date", "")).startswith(month_filter)]
        return jsonify({"transactions": transactions})
    except Exception:
        logger.exception("list_transactions failed")
        return _internal_error()


@app.route("/api/transactions/<id>", methods=["GET"])
@require_auth
def get_transaction(id):
    try:
        hid = _hid()
        transaction = next((t for t in get_all_transactions(hid) if t.get("id") == id), None)
        if not transaction:
            return error_response("Transaction not found.", 404)
        return jsonify(transaction)
    except Exception:
        logger.exception("get_transaction failed")
        return _internal_error()


@app.route("/api/transactions", methods=["POST"])
@require_auth
def add_transaction():
    try:
        hid = _hid()
        payload = request.get_json(silent=True) or {}
        transaction_id = save_transaction(payload, hid)
        transaction = next((t for t in get_all_transactions(hid) if t.get("id") == transaction_id), None)
        return jsonify({"id": transaction_id, "transaction": transaction, "message": "Transaction saved."}), 201
    except Exception:
        logger.exception("add_transaction failed")
        return _internal_error()


@app.route("/api/transactions/batch", methods=["PATCH"])
@require_auth
def batch_patch_transactions():
    try:
        hid = _hid()
        payload = request.get_json(silent=True) or {}
        ids = payload.get("ids", [])
        fields = payload.get("fields", {})
        if not ids:
            return error_response("ids is required.", 400)
        if not fields:
            return error_response("fields is required.", 400)
        count = bulk_update_transactions(ids, fields, hid)
        return jsonify({"updated_count": count, "message": f"Updated {count} transactions."})
    except Exception:
        logger.exception("batch_patch_transactions failed")
        return _internal_error()


@app.route("/api/transactions/<id>", methods=["PATCH"])
@require_auth
def patch_transaction(id):
    try:
        hid = _hid()
        payload = request.get_json(silent=True) or {}
        mutable = {"category", "subcategory", "description", "source", "type", "amount", "date"}
        fields = {k: v for k, v in payload.items() if k in mutable and v is not None}
        if not fields:
            return error_response("At least one editable field is required.", 400)
        if not update_transaction_fields(id, fields, hid):
            return error_response("Transaction not found.", 404)
        transaction = next((t for t in get_all_transactions(hid) if t.get("id") == id), None)
        return jsonify({"id": id, "transaction": transaction, "message": "Transaction updated."})
    except Exception:
        logger.exception("patch_transaction failed")
        return _internal_error()


@app.route("/api/transactions/<id>", methods=["DELETE"])
@require_auth
def remove_transaction(id):
    try:
        hid = _hid()
        if not delete_transaction(id, hid):
            return jsonify({"success": False, "message": "Transaction not found"}), 404
        return jsonify({"success": True, "message": "Transaction deleted"})
    except Exception:
        logger.exception("remove_transaction failed")
        return _internal_error()


@app.route("/api/transactions/clean", methods=["DELETE"])
@require_auth
def clean_transactions():
    try:
        hid = _hid()
        deleted_count = clean_garbage(hid)
        return jsonify({"deleted_count": deleted_count, "message": f"Removed {deleted_count} garbage transactions"})
    except Exception:
        logger.exception("clean_transactions failed")
        return _internal_error()


# ── Summary ───────────────────────────────────────────────────────────────────

@app.route("/api/summary", methods=["GET"])
@require_auth
def summary():
    try:
        return jsonify(rebuild_summary(_hid()))
    except Exception:
        logger.exception("summary failed")
        return _internal_error()


@app.route("/api/categories", methods=["GET"])
@require_auth
def categories():
    try:
        return jsonify(get_categories(_hid()))
    except Exception:
        logger.exception("categories failed")
        return _internal_error()


@app.route("/api/categories/full", methods=["GET"])
@require_auth
def categories_full():
    try:
        return jsonify(get_categories_with_subcategories(_hid()))
    except Exception:
        logger.exception("categories_full failed")
        return _internal_error()


@app.route("/api/categories", methods=["POST"])
@require_auth
def create_category():
    try:
        payload = request.get_json(silent=True) or {}
        name = payload.get("name", "").strip()
        emoji = payload.get("emoji", "🏷️").strip() or "🏷️"
        if not name:
            return error_response("name is required.", 400)
        save_custom_category(name, emoji, household_id=_hid())
        return jsonify({"name": name, "emoji": emoji, "message": "Category saved."}), 201
    except Exception:
        logger.exception("create_category failed")
        return _internal_error()


@app.route("/api/categories/<path:category_name>/subcategories", methods=["POST"])
@require_auth
def create_subcategory(category_name):
    try:
        payload = request.get_json(silent=True) or {}
        subcategory = payload.get("name", "").strip()
        if not subcategory:
            return error_response("name is required.", 400)
        save_custom_subcategory(category_name, subcategory, household_id=_hid())
        return jsonify({"category": category_name, "subcategory": subcategory, "message": "Subcategory saved."}), 201
    except Exception:
        logger.exception("create_subcategory failed")
        return _internal_error()


@app.route("/api/categories/<path:category_name>/subcategories/<path:subcategory_name>", methods=["DELETE"])
@require_auth
def remove_subcategory(category_name, subcategory_name):
    try:
        if not delete_custom_subcategory(category_name, subcategory_name, _hid()):
            return error_response("Subcategory not found or is a built-in subcategory.", 404)
        return jsonify({"message": f"Subcategory '{subcategory_name}' deleted."})
    except Exception:
        logger.exception("remove_subcategory failed")
        return _internal_error()


@app.route("/api/categories/<path:category_name>", methods=["DELETE"])
@require_auth
def remove_category(category_name):
    try:
        if not delete_category(category_name, _hid()):
            return error_response("Category name is required.", 400)
        return jsonify({"message": f"Category '{category_name}' deleted."})
    except Exception:
        logger.exception("remove_category failed")
        return _internal_error()


@app.route("/api/users", methods=["GET"])
@require_auth
def users():
    try:
        return jsonify(get_all_users(_hid()))
    except Exception:
        logger.exception("users failed")
        return _internal_error()


@app.route("/api/transactions/user/<int:logged_by_id>", methods=["GET"])
@require_auth
def transactions_by_user(logged_by_id):
    try:
        return jsonify({"transactions": get_transactions_by_user(logged_by_id, _hid())})
    except Exception:
        logger.exception("transactions_by_user failed")
        return _internal_error()


@app.route("/api/summary/user/<int:logged_by_id>", methods=["GET"])
@require_auth
def summary_by_user(logged_by_id):
    try:
        return jsonify(get_user_summary(logged_by_id, _hid()))
    except Exception:
        logger.exception("summary_by_user failed")
        return _internal_error()


@app.route("/api/summary/monthly", methods=["GET"])
@require_auth
def monthly_summary():
    try:
        return jsonify(get_summary(_hid()).get("monthly_totals", {}))
    except Exception:
        logger.exception("monthly_summary failed")
        return _internal_error()


@app.route("/api/summary/categories", methods=["GET"])
@require_auth
def category_summary():
    try:
        return jsonify(get_summary(_hid()).get("category_totals", {}))
    except Exception:
        logger.exception("category_summary failed")
        return _internal_error()


# ── Export ────────────────────────────────────────────────────────────────────

@app.route("/api/export/csv", methods=["GET"])
@require_auth
def export_csv():
    try:
        return send_file(transaction_csv_path(_hid()), as_attachment=True, download_name="transactions.csv", mimetype="text/csv")
    except Exception:
        logger.exception("export_csv failed")
        return _internal_error()


@app.route("/api/export/monthly/<int:year>/<int:month>", methods=["GET"])
@require_auth
def export_monthly(year, month):
    try:
        if not (1 <= month <= 12):
            return error_response("Month must be between 1 and 12.", 400)
        if not (2000 <= year <= 2100):
            return error_response("Year must be between 2000 and 2100.", 400)
        csv_text = export_monthly_report(year, month, _hid())
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
@require_auth
def parse_text():
    try:
        hid = _hid()
        payload = request.get_json(silent=True) or {}
        message = payload.get("message", "")
        if not message:
            return error_response("message is required.", 400)
        all_categories = get_categories_with_subcategories(hid)
        result = extract_from_text(message, all_categories=all_categories)
        return jsonify({"transactions": result.get("transactions", []), "query": result.get("query")})
    except Exception:
        logger.exception("parse_text failed")
        return _internal_error()


@app.route("/api/parse/image", methods=["POST"])
@require_auth
def parse_image():
    try:
        hid = _hid()
        file = request.files.get("image") or request.files.get("file")
        if not file:
            return error_response("image file is required.", 400)
        image_bytes, mime_type = _validate_image_file(file)
        all_categories = get_categories_with_subcategories(hid)
        transactions = extract_from_image(image_bytes, mime_type, all_categories=all_categories)
        return jsonify({"transactions": transactions})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        logger.exception("parse_image failed")
        return _internal_error()


@app.route("/api/parse/pdf", methods=["POST"])
@require_auth
def parse_pdf():
    try:
        hid = _hid()
        file = request.files.get("pdf") or request.files.get("file")
        if not file:
            return error_response("pdf file is required.", 400)
        pdf_bytes = _validate_pdf_file(file)
        all_categories = get_categories_with_subcategories(hid)
        transactions = extract_from_pdf(pdf_bytes, all_categories=all_categories)
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
