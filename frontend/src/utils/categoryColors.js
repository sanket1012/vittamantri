const CATEGORY_COLORS = {
  'Food & Dining':    '#EA580C',
  'Groceries':        '#16A34A',
  'Transport':        '#0891B2',
  'Rent & Housing':   '#7C3AED',
  'Health & Medical': '#DC2626',
  'Entertainment':    '#DB2777',
  'Shopping':         '#D97706',
  'Subscriptions':    '#4F46E5',
  'Education':        '#2563EB',
  'EMI & Loans':      '#BE123C',
  'Investment & SIP': '#059669',
  'Salary & Income':  '#047857',
  'Gifts & Misc':     '#6B7280',
  'Utilities & Bills':'#0369A1',
};

const FALLBACK_COLORS = [
  '#004EEB', '#059669', '#DC2626', '#F59E0B', '#7C3AED',
  '#0891B2', '#DB2777', '#65A30D', '#EA580C', '#4F46E5',
  '#0D9488', '#9333EA', '#BE123C', '#2563EB',
];

function hashName(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h) + str.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export function getCategoryColor(name) {
  if (!name) return '#667085';
  return CATEGORY_COLORS[name] ?? FALLBACK_COLORS[hashName(name) % FALLBACK_COLORS.length];
}
