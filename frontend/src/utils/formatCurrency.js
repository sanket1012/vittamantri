// Compact Indian-style currency for chart axes/labels — avoids arbitrarily
// wide strings (e.g. "₹987654.321k") that overflow a chart's reserved axis
// width. Full formatINR (with commas) stays in each component for tooltips
// and card values, where the full precision is wanted.
export function formatCompactINR(amount = 0) {
  const value = Number(amount || 0);
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (abs >= 1_00_00_000) return `${sign}₹${(abs / 1_00_00_000).toFixed(1)}Cr`;
  if (abs >= 1_00_000) return `${sign}₹${(abs / 1_00_000).toFixed(1)}L`;
  if (abs >= 1_000) return `${sign}₹${(abs / 1_000).toFixed(1)}k`;
  return `${sign}₹${abs}`;
}
