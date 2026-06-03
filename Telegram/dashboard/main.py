import sys
import os

# Allow importing finance_db from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import finance_db

finance_db.init_db()

app = FastAPI(title="Finance Dashboard API")


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


@app.get("/api/summary")
def summary(month: str = Query(default=None)):
    m = month or current_month()
    data = finance_db.get_summary(user_id=None, month=m)
    data["month"] = m
    return JSONResponse(data)


@app.get("/api/transactions")
def transactions(
    month: str = Query(default=None),
    limit: int = Query(default=200),
):
    m = month or current_month()
    rows = finance_db.get_transactions(user_id=None, month=m, limit=limit)
    return JSONResponse({"transactions": rows, "month": m})


@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    deleted = finance_db.soft_delete_transaction(transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return JSONResponse({"ok": True, "id": transaction_id})


@app.get("/api/monthly_totals")
def monthly_totals(n: int = Query(default=6)):
    data = finance_db.get_monthly_totals(user_id=None, n_months=n)
    return JSONResponse({"monthly_totals": data})


@app.get("/api/categories")
def categories(month: str = Query(default=None)):
    m = month or current_month()
    summary = finance_db.get_summary(user_id=None, month=m)
    return JSONResponse({"categories": summary["by_category"], "month": m})


@app.get("/api/goals")
def goals():
    # Show goals for all users (shared household)
    import sqlite3
    conn = sqlite3.connect(finance_db.DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM financial_goals WHERE status='active' ORDER BY target_date NULLS LAST"
    ).fetchall()
    conn.close()
    return JSONResponse({"goals": [dict(r) for r in rows]})


@app.get("/api/plans")
def plans():
    import sqlite3
    conn = sqlite3.connect(finance_db.DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM planned_expenses WHERE status='pending' ORDER BY planned_date"
    ).fetchall()
    conn.close()
    return JSONResponse({"plans": [dict(r) for r in rows]})


@app.get("/api/months")
def available_months():
    """Returns all months that have at least one transaction."""
    import sqlite3
    conn = sqlite3.connect(finance_db.DB_PATH)
    rows = conn.execute(
        "SELECT DISTINCT substr(date,1,7) AS month FROM transactions "
        "WHERE deleted=0 ORDER BY month DESC"
    ).fetchall()
    conn.close()
    return JSONResponse({"months": [r[0] for r in rows]})


# Serve the single-page app — must be mounted last
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
