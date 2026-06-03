from datetime import datetime


def build_summary_text(summary: dict, month: str, dashboard_url: str = "http://localhost:8080") -> str:
    net = summary["net_balance"]
    net_sign = "+" if net >= 0 else ""
    month_label = _month_label(month)

    lines = [
        f"<b>Balance Sheet — {month_label}</b>",
        "",
        f"Income:    ₹{summary['total_income']:,.0f}",
        f"Expenses:  ₹{summary['total_expenses']:,.0f}",
        f"Net:       <b>{net_sign}₹{net:,.0f}</b>",
    ]

    expense_cats = [c for c in summary["by_category"] if c["type"] == "expense"]
    if expense_cats:
        lines += ["", "<b>Top Expenses</b>"]
        for c in expense_cats[:6]:
            lines.append(f"  {c['category']:<18} ₹{c['total']:>8,.0f}")

    lines += ["", f'<a href="{dashboard_url}">View full dashboard</a>']
    return "\n".join(lines)


def build_history_text(transactions: list[dict]) -> str:
    if not transactions:
        return "No transactions recorded yet."
    lines = ["<b>Recent Transactions</b>", ""]
    for t in transactions:
        sign = "-" if t["type"] == "expense" else "+"
        desc = f"  {t['description']}" if t.get("description") else ""
        lines.append(
            f"{t['date']}  <b>{t['category']}</b>  {sign}₹{t['amount']:,.0f}{desc}"
        )
    return "\n".join(lines)


def build_confirmation_text(transactions: list[dict], recurring_ids: list | None = None) -> str:
    if not transactions:
        return "No transactions found."
    lines = ["Recorded:"]
    for i, t in enumerate(transactions):
        sign = "-" if t["type"] == "expense" else "+"
        desc = f" · {t['description']}" if t.get("description") else ""
        is_recurring = t.get("recurring") and t.get("frequency")
        freq_tag = f" 🔁 {t['frequency']}" if is_recurring else ""
        date_tag = f" ({t['date']})" if not is_recurring else ""
        lines.append(f"  {sign}₹{t['amount']:,.0f} · {t['category']}{desc}{freq_tag}{date_tag}")
    return "\n".join(lines)


def _month_label(month: str) -> str:
    if month == "all":
        return "All Time"
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    except ValueError:
        return month
