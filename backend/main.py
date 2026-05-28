import os
import logging
from io import StringIO

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS

from data_manager import (
    clean_garbage,
    delete_transaction,
    export_monthly_report,
    get_all_transactions,
    get_all_users,
    get_categories,
    get_summary,
    get_transactions_by_month,
    get_transactions_by_user,
    get_user_summary,
    rebuild_summary,
    save_transaction,
    transaction_csv_path,
)
from gemini_parser import extract_from_image, extract_from_pdf
from groq_parser import extract_from_text

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vittamantri.api")

app = Flask(__name__)
CORS(app, origins=[os.getenv("FRONTEND_URL", "http://localhost:5173"), "http://localhost:5173", "http://localhost:3000"])


def error_response(message: str, status: int = 400):
    return jsonify({"error": message}), status


@app.route("/")
def health_check():
    return jsonify({"status": "वित्तमंत्री is running"})


@app.route("/api/transactions", methods=["GET"])
def list_transactions():
    try:
        month_filter = request.args.get("month")
        transactions = get_all_transactions()
        if month_filter:
            transactions = [item for item in transactions if str(item.get("date", "")).startswith(month_filter)]
        return jsonify({"transactions": transactions})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/transactions/<id>", methods=["GET"])
def get_transaction(id):
    try:
        transaction = next((item for item in get_all_transactions() if item.get("id") == id), None)
        if not transaction:
            return error_response("Transaction not found.", 404)
        return jsonify(transaction)
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    try:
        payload = request.get_json(silent=True) or {}
        transaction_id = save_transaction(payload)
        transaction = next((item for item in get_all_transactions() if item.get("id") == transaction_id), None)
        return jsonify({"id": transaction_id, "transaction": transaction, "message": "Transaction saved."}), 201
    except Exception as exc:
        return error_response(str(exc), 400)


@app.route("/api/transactions/<id>", methods=["DELETE"])
def remove_transaction(id):
    try:
        if not delete_transaction(id):
            return jsonify({"success": False, "message": "Transaction not found"}), 404
        return jsonify({"success": True, "message": "Transaction deleted"})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/transactions/clean", methods=["DELETE"])
def clean_transactions():
    try:
        deleted_count = clean_garbage()
        return jsonify({"deleted_count": deleted_count, "message": f"Removed {deleted_count} garbage transactions"})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/summary", methods=["GET"])
def summary():
    try:
        return jsonify(rebuild_summary())
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/categories", methods=["GET"])
def categories():
    try:
        return jsonify(get_categories())
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/users", methods=["GET"])
def users():
    try:
        return jsonify(get_all_users())
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/transactions/user/<int:logged_by_id>", methods=["GET"])
def transactions_by_user(logged_by_id):
    try:
        return jsonify({"transactions": get_transactions_by_user(logged_by_id)})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/summary/user/<int:logged_by_id>", methods=["GET"])
def summary_by_user(logged_by_id):
    try:
        return jsonify(get_user_summary(logged_by_id))
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/summary/monthly", methods=["GET"])
def monthly_summary():
    try:
        return jsonify(get_summary().get("monthly_totals", {}))
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/summary/categories", methods=["GET"])
def category_summary():
    try:
        return jsonify(get_summary().get("category_totals", {}))
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    try:
        return send_file(transaction_csv_path(), as_attachment=True, download_name="transactions.csv", mimetype="text/csv")
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/export/monthly/<int:year>/<int:month>", methods=["GET"])
def export_monthly(year, month):
    try:
        if month < 1 or month > 12:
            return error_response("Month must be between 1 and 12.", 400)
        csv_text = export_monthly_report(year, month)
        return Response(
            csv_text,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=vittamantri-{year}-{month:02d}.csv"},
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/parse/text", methods=["POST"])
def parse_text():
    try:
        payload = request.get_json(silent=True) or {}
        message = payload.get("message", "")
        if not message:
            return error_response("message is required.", 400)
        extracted = extract_from_text(message)
        return jsonify({"transaction": extracted})
    except Exception as exc:
        return error_response(str(exc), 400)


@app.route("/api/parse/image", methods=["POST"])
def parse_image():
    try:
        file = request.files.get("image") or request.files.get("file")
        if not file:
            return error_response("image file is required.", 400)
        image_bytes = file.read()
        mime_type = file.mimetype or "image/jpeg"
        transactions = extract_from_image(image_bytes, mime_type)
        return jsonify({"transactions": transactions})
    except Exception as exc:
        logger.exception("Image parse failed")
        return error_response(str(exc), 400)


@app.route("/api/parse/pdf", methods=["POST"])
def parse_pdf():
    try:
        file = request.files.get("pdf") or request.files.get("file")
        if not file:
            return error_response("pdf file is required.", 400)
        pdf_bytes = file.read()
        transactions = extract_from_pdf(pdf_bytes)
        return jsonify({"transactions": transactions})
    except Exception as exc:
        logger.exception("PDF parse failed")
        return error_response(str(exc), 400)


if __name__ == "__main__":
    app.run(debug=True, port=8000, use_reloader=False)
