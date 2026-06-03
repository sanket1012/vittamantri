"""
Financial advisor module — CA persona with injected live financial context.
Maintains a separate per-user conversation history from the general assistant.
"""

from collections import defaultdict
from groq import Groq
import os

MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 16

ADVISOR_SYSTEM_TEMPLATE = """\
You are Sanket's personal Chartered Accountant and financial advisor.

## Live Financial Snapshot

### This Month ({month})
- Income:   ₹{income:,.0f}
- Expenses: ₹{expenses:,.0f}
- Net:      ₹{net:,.0f}  ({savings_rate:.0f}% savings rate)

### Spending by Category
{category_breakdown}

### 3-Month Trend
{trend}

### Active Financial Goals
{goals}

### Upcoming Planned Expenses
{plans}

### Recent Transactions (last 10)
{recent_txns}

---

## Your Role
- Give specific, numbers-backed advice — reference actual amounts above, not vague advice
- Help Sanket and his family stay on track toward goals; flag if current spending jeopardises them
- Flag overspending in any category compared to income or stated goals
- Suggest investment allocation for available surplus (Indian context: SIP/mutual funds, ELSS for 80C, PPF, NPS, FD)
- Plan for upcoming large expenses — ensure sufficient buffer is being built
- Apply Indian tax-saving strategies where relevant (FY April–March)
- Keep responses concise and actionable — lead with the most important insight

Tone: professional but direct. Use actual ₹ numbers. Don't soften hard truths about overspending.
"""

_advisor_histories: dict[int, list[dict]] = defaultdict(list)


def _fmt_categories(by_category: list[dict]) -> str:
    lines = []
    for c in by_category[:8]:
        sign = "-" if c["type"] == "expense" else "+"
        lines.append(f"  {c['category']:<20} {sign}₹{c['total']:>9,.0f}")
    return "\n".join(lines) if lines else "  No data yet"


def _fmt_trend(trend: list[dict]) -> str:
    if not trend:
        return "  No data yet"
    lines = []
    for m in trend:
        net = m.get("income", 0) - m.get("expenses", 0)
        sign = "+" if net >= 0 else ""
        lines.append(f"  {m['month']}  Income ₹{m.get('income',0):,.0f}  Expenses ₹{m.get('expenses',0):,.0f}  Net {sign}₹{net:,.0f}")
    return "\n".join(lines)


def _fmt_goals(goals: list[dict]) -> str:
    if not goals:
        return "  No active goals set. (User can set goals via natural language, e.g. 'Save 200000 for vacation by December')"
    lines = []
    for g in goals:
        date_str = f" by {g['target_date']}" if g.get("target_date") else ""
        lines.append(f"  [{g['id']}] {g['name']}: ₹{g['target_amount']:,.0f}{date_str} — {g['category']}")
        if g.get("notes"):
            lines.append(f"       Note: {g['notes']}")
    return "\n".join(lines)


def _fmt_plans(plans: list[dict]) -> str:
    if not plans:
        return "  No planned expenses. (User can add via natural language, e.g. 'Planning to buy laptop for 80000 in June')"
    lines = []
    for p in plans:
        lines.append(f"  [{p['id']}] {p['name']}: ₹{p['amount']:,.0f} on {p['planned_date']} — {p['category']}")
    return "\n".join(lines)


def _fmt_recent(txns: list[dict]) -> str:
    if not txns:
        return "  No transactions recorded yet"
    lines = []
    for t in txns[:10]:
        sign = "-" if t["type"] == "expense" else "+"
        lines.append(f"  {t['date']}  {t['category']:<16} {sign}₹{t['amount']:,.0f}  {t.get('description','')[:30]}")
    return "\n".join(lines)


def build_system_prompt(ctx: dict) -> str:
    ms = ctx["monthly_summary"]
    income = ms["total_income"]
    expenses = ms["total_expenses"]
    net = ms["net_balance"]
    savings_rate = (net / income * 100) if income > 0 else 0

    return ADVISOR_SYSTEM_TEMPLATE.format(
        month=ms.get("month", "current"),
        income=income,
        expenses=expenses,
        net=net,
        savings_rate=savings_rate,
        category_breakdown=_fmt_categories(ms["by_category"]),
        trend=_fmt_trend(ctx["trend"]),
        goals=_fmt_goals(ctx["goals"]),
        plans=_fmt_plans(ctx["plans"]),
        recent_txns=_fmt_recent(ctx["recent_transactions"]),
    )


def advise(user_id: int, user_message: str, ctx: dict, groq_client: Groq) -> str:
    system_prompt = build_system_prompt(ctx)
    history = _advisor_histories[user_id]
    history.append({"role": "user", "content": user_message})

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt}] + history,
        temperature=0.5,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})

    if len(history) > MAX_HISTORY:
        _advisor_histories[user_id] = history[-MAX_HISTORY:]

    return reply


def clear_advisor_history(user_id: int) -> None:
    _advisor_histories[user_id] = []
