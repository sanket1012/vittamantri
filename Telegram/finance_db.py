import sqlite3
import threading
from datetime import datetime, date, timedelta

DB_PATH = "finance.db"

_local = threading.local()


def _conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def init_db() -> None:
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            date        TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            type        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT    NOT NULL DEFAULT '',
            source      TEXT    NOT NULL DEFAULT 'text',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            deleted     INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_user_date  ON transactions(user_id, date);
        CREATE INDEX IF NOT EXISTS idx_user_month ON transactions(user_id, substr(date,1,7));

        CREATE TABLE IF NOT EXISTS recurring_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL    NOT NULL,
            type        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT    NOT NULL DEFAULT '',
            frequency   TEXT    NOT NULL,  -- 'daily' | 'weekly' | 'monthly'
            next_run    TEXT    NOT NULL,  -- 'YYYY-MM-DD'
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            active      INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS financial_goals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            name            TEXT    NOT NULL,
            target_amount   REAL    NOT NULL,
            target_date     TEXT,               -- 'YYYY-MM-DD' or NULL
            category        TEXT    NOT NULL DEFAULT 'Savings',
            notes           TEXT    NOT NULL DEFAULT '',
            status          TEXT    NOT NULL DEFAULT 'active',  -- 'active' | 'achieved' | 'cancelled'
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS planned_expenses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            name            TEXT    NOT NULL,
            amount          REAL    NOT NULL,
            planned_date    TEXT    NOT NULL,   -- 'YYYY-MM-DD'
            category        TEXT    NOT NULL,
            notes           TEXT    NOT NULL DEFAULT '',
            status          TEXT    NOT NULL DEFAULT 'pending',  -- 'pending' | 'done' | 'cancelled'
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """)
    c.commit()


def add_transaction(
    user_id: int,
    date_: str,
    amount: float,
    type_: str,
    category: str,
    description: str,
    source: str = "text",
) -> int:
    c = _conn()
    cur = c.execute(
        "INSERT INTO transactions (user_id, date, amount, type, category, description, source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, date_, amount, type_, category, description, source),
    )
    c.commit()
    return cur.lastrowid


def _user_filter(user_id: int | None) -> tuple[str, list]:
    """Returns (WHERE clause fragment, params) for optional user_id filtering."""
    if user_id is None:
        return "deleted=0", []
    return "user_id=? AND deleted=0", [user_id]


def get_transactions(
    user_id: int | None = None,
    month: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    c = _conn()
    where, params = _user_filter(user_id)
    if month:
        where += " AND substr(date,1,7)=?"
        params.append(month)
    sql = f"SELECT * FROM transactions WHERE {where} ORDER BY date DESC, id DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = c.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_summary(user_id: int | None = None, month: str | None = None) -> dict:
    c = _conn()
    where, params = _user_filter(user_id)
    if month:
        where += " AND substr(date,1,7)=?"
        params.append(month)

    row = c.execute(
        f"SELECT "
        f"  COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END), 0) AS income, "
        f"  COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS expenses "
        f"FROM transactions WHERE {where}",
        params,
    ).fetchone()

    by_cat = c.execute(
        f"SELECT category, type, SUM(amount) AS total "
        f"FROM transactions WHERE {where} "
        f"GROUP BY category, type ORDER BY total DESC",
        params,
    ).fetchall()

    return {
        "total_income": row["income"],
        "total_expenses": row["expenses"],
        "net_balance": row["income"] - row["expenses"],
        "by_category": [dict(r) for r in by_cat],
        "month": month or "all",
    }


def get_monthly_totals(user_id: int | None = None, n_months: int = 6) -> list[dict]:
    c = _conn()
    where, params = _user_filter(user_id)
    rows = c.execute(
        f"SELECT substr(date,1,7) AS month, type, SUM(amount) AS total "
        f"FROM transactions WHERE {where} "
        f"GROUP BY month, type ORDER BY month DESC LIMIT {n_months * 2}",
        params,
    ).fetchall()
    pivot: dict[str, dict] = {}
    for r in rows:
        m = r["month"]
        if m not in pivot:
            pivot[m] = {"month": m, "income": 0.0, "expenses": 0.0}
        pivot[m]["income" if r["type"] == "income" else "expenses"] += r["total"]
    return sorted(pivot.values(), key=lambda x: x["month"])[-n_months:]


def get_last_transaction_id(user_id: int) -> int | None:
    c = _conn()
    row = c.execute(
        "SELECT id FROM transactions WHERE user_id=? AND deleted=0 ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return row["id"] if row else None


def soft_delete_transaction(transaction_id: int) -> bool:
    c = _conn()
    cur = c.execute(
        "UPDATE transactions SET deleted=1 WHERE id=? AND deleted=0",
        (transaction_id,),
    )
    c.commit()
    return cur.rowcount > 0


def get_all_categories(user_id: int) -> list[str]:
    c = _conn()
    rows = c.execute(
        "SELECT DISTINCT category FROM transactions WHERE user_id=? AND deleted=0 ORDER BY category",
        (user_id,),
    ).fetchall()
    return [r["category"] for r in rows]


# ── Recurring transactions ─────────────────────────────────────────────────────

def _next_run_date(from_date: str, frequency: str) -> str:
    from datetime import timedelta
    d = date.fromisoformat(from_date)
    if frequency == "daily":
        d += timedelta(days=1)
    elif frequency == "weekly":
        d += timedelta(weeks=1)
    elif frequency == "monthly":
        month = d.month + 1
        year = d.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(d.day, [31,29 if year%4==0 and (year%100!=0 or year%400==0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
        d = d.replace(year=year, month=month, day=day)
    return d.isoformat()


def add_recurring(
    user_id: int,
    amount: float,
    type_: str,
    category: str,
    description: str,
    frequency: str,
    start_date: str,
) -> int:
    c = _conn()
    cur = c.execute(
        "INSERT INTO recurring_transactions (user_id, amount, type, category, description, frequency, next_run) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, amount, type_, category, description, frequency, start_date),
    )
    c.commit()
    return cur.lastrowid


def get_recurring(user_id: int) -> list[dict]:
    c = _conn()
    rows = c.execute(
        "SELECT * FROM recurring_transactions WHERE user_id=? AND active=1 ORDER BY next_run",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def cancel_recurring(recurring_id: int, user_id: int) -> bool:
    c = _conn()
    cur = c.execute(
        "UPDATE recurring_transactions SET active=0 WHERE id=? AND user_id=? AND active=1",
        (recurring_id, user_id),
    )
    c.commit()
    return cur.rowcount > 0


def get_due_recurring(as_of: str) -> list[dict]:
    """Returns all active recurring entries due on or before as_of date."""
    c = _conn()
    rows = c.execute(
        "SELECT * FROM recurring_transactions WHERE active=1 AND next_run<=? ORDER BY next_run",
        (as_of,),
    ).fetchall()
    return [dict(r) for r in rows]


def advance_recurring(recurring_id: int, current_next_run: str, frequency: str) -> None:
    """Bumps next_run to the following occurrence after current_next_run."""
    c = _conn()
    new_next = _next_run_date(current_next_run, frequency)
    c.execute(
        "UPDATE recurring_transactions SET next_run=? WHERE id=?",
        (new_next, recurring_id),
    )
    c.commit()


# ── Financial goals ────────────────────────────────────────────────────────────

def add_goal(
    user_id: int,
    name: str,
    target_amount: float,
    target_date: str | None,
    category: str = "Savings",
    notes: str = "",
) -> int:
    c = _conn()
    cur = c.execute(
        "INSERT INTO financial_goals (user_id, name, target_amount, target_date, category, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, target_amount, target_date, category, notes),
    )
    c.commit()
    return cur.lastrowid


def get_goals(user_id: int, status: str = "active") -> list[dict]:
    c = _conn()
    rows = c.execute(
        "SELECT * FROM financial_goals WHERE user_id=? AND status=? ORDER BY target_date NULLS LAST",
        (user_id, status),
    ).fetchall()
    return [dict(r) for r in rows]


def cancel_goal(goal_id: int, user_id: int) -> bool:
    c = _conn()
    cur = c.execute(
        "UPDATE financial_goals SET status='cancelled' WHERE id=? AND user_id=? AND status='active'",
        (goal_id, user_id),
    )
    c.commit()
    return cur.rowcount > 0


def mark_goal_achieved(goal_id: int, user_id: int) -> bool:
    c = _conn()
    cur = c.execute(
        "UPDATE financial_goals SET status='achieved' WHERE id=? AND user_id=?",
        (goal_id, user_id),
    )
    c.commit()
    return cur.rowcount > 0


# ── Planned expenses ───────────────────────────────────────────────────────────

def add_plan(
    user_id: int,
    name: str,
    amount: float,
    planned_date: str,
    category: str,
    notes: str = "",
) -> int:
    c = _conn()
    cur = c.execute(
        "INSERT INTO planned_expenses (user_id, name, amount, planned_date, category, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, amount, planned_date, category, notes),
    )
    c.commit()
    return cur.lastrowid


def get_plans(user_id: int, status: str = "pending") -> list[dict]:
    c = _conn()
    rows = c.execute(
        "SELECT * FROM planned_expenses WHERE user_id=? AND status=? ORDER BY planned_date",
        (user_id, status),
    ).fetchall()
    return [dict(r) for r in rows]


def cancel_plan(plan_id: int, user_id: int) -> bool:
    c = _conn()
    cur = c.execute(
        "UPDATE planned_expenses SET status='cancelled' WHERE id=? AND user_id=? AND status='pending'",
        (plan_id, user_id),
    )
    c.commit()
    return cur.rowcount > 0


def get_advisor_context(user_id: int) -> dict:
    """Builds a rich financial context snapshot for the AI advisor."""
    summary_month = get_summary(user_id=None, month=datetime.now().strftime("%Y-%m"))
    trend = get_monthly_totals(user_id=None, n_months=3)
    goals = get_goals(user_id, status="active")
    plans = get_plans(user_id, status="pending")
    recent_txns = get_transactions(user_id=None, limit=10)
    return {
        "monthly_summary": summary_month,
        "trend": trend,
        "goals": goals,
        "plans": plans,
        "recent_transactions": recent_txns,
    }
