/** Builds a daily income/expense/balance series for the trailing N days — used
 * for sparklines. Balance is cumulative across the window, not a running
 * all-time balance, so short sparklines still show a meaningful shape. */
export function buildDailyTrend(transactions, days = 14) {
  const today = new Date();
  const buckets = Array.from({ length: days }, (_, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() - (days - 1 - index));
    return { key: date.toISOString().slice(0, 10), income: 0, expense: 0 };
  });
  const byDate = Object.fromEntries(buckets.map((day) => [day.key, day]));
  transactions.forEach((item) => {
    const bucket = byDate[item.date];
    if (!bucket) return;
    if (item.type === 'income') bucket.income += Number(item.amount || 0);
    if (item.type === 'expense') bucket.expense += Number(item.amount || 0);
  });

  let running = 0;
  return buckets.map((day) => {
    running += day.income - day.expense;
    return { ...day, balance: running };
  });
}

const monthKey = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

/** Builds a monthly income/expense series for the trailing N months (inclusive
 * of the current month) — used for the Cash Flow chart. */
export function buildMonthlyTrend(transactions, months = 6) {
  const now = new Date();
  const keys = Array.from({ length: months }, (_, index) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (months - 1 - index), 1);
    return { key: monthKey(d), label: d.toLocaleDateString('en-IN', { month: 'short' }) };
  });
  const totals = Object.fromEntries(keys.map(({ key, label }) => [key, { month: label, income: 0, expense: 0 }]));
  transactions.forEach((item) => {
    const key = (item.date || '').slice(0, 7);
    if (!totals[key]) return;
    if (item.type === 'income') totals[key].income += Number(item.amount || 0);
    if (item.type === 'expense') totals[key].expense += Number(item.amount || 0);
  });
  return keys.map(({ key }) => totals[key]);
}

/** Percentage change from `previous` to `current`, or null when there's
 * nothing meaningful to compare against (caller should hide the delta). */
export function percentChange(current, previous) {
  if (!previous) return null;
  return ((current - previous) / previous) * 100;
}
