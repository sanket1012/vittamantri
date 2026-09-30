import { useMemo } from 'react';
import InsightsIcon from '@mui/icons-material/Insights';
import SavingsIcon from '@mui/icons-material/Savings';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { Box, Card, CardContent, Skeleton, Typography } from '@mui/material';
import { percentChange } from '../utils/trends.js';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

const monthKey = (offset = 0) => {
  const d = new Date();
  d.setMonth(d.getMonth() + offset);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};

function buildInsights(transactions, summary) {
  const insights = [];
  const thisMonth = monthKey(0);
  const thisMonthTxns = transactions.filter((t) => (t.date || '').slice(0, 7) === thisMonth);

  // 1. Income change vs last month (only when we have a comparable prior total)
  const prevIncome = summary?.monthly_totals?.[monthKey(-1)]?.income;
  const thisIncome = thisMonthTxns.filter((t) => t.type === 'income').reduce((s, t) => s + Number(t.amount || 0), 0);
  const incomeChange = prevIncome ? percentChange(thisIncome, prevIncome) : null;
  if (incomeChange !== null) {
    insights.push({
      icon: incomeChange >= 0 ? TrendingUpIcon : TrendingDownIcon,
      color: incomeChange >= 0 ? '#243044' : '#D96B67',
      text: `Income ${incomeChange >= 0 ? 'increased' : 'decreased'} ${Math.abs(incomeChange).toFixed(0)}% this month`,
    });
  }

  // 2. Savings this month
  const thisExpense = thisMonthTxns.filter((t) => t.type === 'expense').reduce((s, t) => s + Number(t.amount || 0), 0);
  const savings = thisIncome - thisExpense;
  if (thisIncome > 0) {
    const rate = (savings / thisIncome) * 100;
    insights.push({
      icon: SavingsIcon,
      color: '#111827',
      text: `You've saved ${formatINR(savings)} — ${rate.toFixed(0)}% of this month's income`,
    });
  }

  // 3. Category vs its own trailing 3-month average
  const thisMonthByCategory = {};
  thisMonthTxns.filter((t) => t.type === 'expense').forEach((t) => {
    const cat = t.category || 'Uncategorized';
    thisMonthByCategory[cat] = (thisMonthByCategory[cat] || 0) + Number(t.amount || 0);
  });
  const topCategory = Object.entries(thisMonthByCategory).sort((a, b) => b[1] - a[1])[0];
  if (topCategory) {
    const [category, amount] = topCategory;
    const priorMonths = [monthKey(-1), monthKey(-2), monthKey(-3)];
    const priorTotals = priorMonths.map((key) =>
      transactions
        .filter((t) => t.type === 'expense' && t.category === category && (t.date || '').slice(0, 7) === key)
        .reduce((s, t) => s + Number(t.amount || 0), 0),
    );
    const monthsWithData = priorTotals.filter((v) => v > 0);
    if (monthsWithData.length) {
      const avg = monthsWithData.reduce((s, v) => s + v, 0) / monthsWithData.length;
      const diff = percentChange(amount, avg);
      if (diff !== null && Math.abs(diff) >= 5) {
        insights.push({
          icon: diff >= 0 ? TrendingUpIcon : TrendingDownIcon,
          color: diff >= 0 ? '#D96B67' : '#243044',
          text: `${category} spending is ${Math.abs(diff).toFixed(0)}% ${diff >= 0 ? 'higher' : 'lower'} than your 3-month average`,
        });
      }
    }
    if (insights.length < 3) {
      insights.push({ icon: InsightsIcon, color: '#111827', text: `Largest spend this month: ${category} (${formatINR(amount)})` });
    }
  }

  return insights;
}

export default function FinancialInsights({ transactions = [], summary, loading }) {
  const insights = useMemo(() => buildInsights(transactions, summary), [transactions, summary]);

  return (
    <Card sx={{ height: '100%' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #E3DDD4', display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box component="span" sx={{ color: '#6E72AE', fontSize: 16, lineHeight: 1 }}>✦</Box>
        <Box>
          <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#20242C' }}>Samvitta Insight</Typography>
          <Typography sx={{ fontSize: '0.875rem', color: '#77736D' }}>What Samvitta noticed in your household activity</Typography>
        </Box>
      </Box>
      <CardContent sx={{ p: 3, display: 'grid', gap: 2 }}>
        {loading ? (
          <>
            <Skeleton variant="rounded" height={48} />
            <Skeleton variant="rounded" height={48} />
          </>
        ) : insights.length ? (
          insights.map((insight, index) => {
            const Icon = insight.icon;
            return (
              <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                <Box sx={{ width: 32, height: 32, borderRadius: '9px', bgcolor: `${insight.color}14`, color: insight.color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon sx={{ fontSize: 18 }} />
                </Box>
                <Typography sx={{ fontSize: '0.875rem', color: '#20242C', lineHeight: 1.4, pt: '4px' }}>{insight.text}</Typography>
              </Box>
            );
          })
        ) : (
          <Box>
            <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#20242C', mb: 0.5 }}>No insights yet</Typography>
            <Typography sx={{ fontSize: '0.875rem', color: '#77736D', lineHeight: 1.5 }}>
              Once Samvitta has enough transaction history, it will start identifying trends and unusual changes.
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
