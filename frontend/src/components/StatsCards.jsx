import { useMemo } from 'react';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import { Box, Card, CardContent, Grid, Skeleton, Typography } from '@mui/material';
import { buildDailyTrend, percentChange } from '../utils/trends.js';
import Sparkline from './Sparkline.jsx';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2,
  }).format(Number(amount || 0));

function buildStats(summary, transactions, selectedUserId, activeMonth) {
  const rows = selectedUserId !== 'All'
    ? transactions.filter((item) => String(item.logged_by_id || '0') === String(selectedUserId))
    : transactions;

  if (selectedUserId !== 'All' || activeMonth) {
    const income = rows.filter((item) => item.type === 'income').reduce((sum, item) => sum + Number(item.amount || 0), 0);
    const expense = rows.filter((item) => item.type === 'expense').reduce((sum, item) => sum + Number(item.amount || 0), 0);
    return { income, expense, balance: income - expense, count: rows.length };
  }

  return {
    income: Number(summary?.total_income || 0),
    expense: Number(summary?.total_expense || 0),
    balance: Number(summary?.net_savings || 0),
    count: Number(summary?.transaction_count || transactions.length || 0),
  };
}

// Only meaningful for the unfiltered, all-time/current-month view — a
// specific user or historical month doesn't have a comparable prior-month
// total from the API, so callers should treat a null return as "hide it".
function previousMonthTotals(summary, selectedUserId, activeMonth) {
  if (selectedUserId !== 'All' || activeMonth) return null;
  const monthly = summary?.monthly_totals;
  if (!monthly) return null;
  const now = new Date();
  const prev = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const key = `${prev.getFullYear()}-${String(prev.getMonth() + 1).padStart(2, '0')}`;
  return monthly[key] || null;
}

function DeltaBadge({ direction, label }) {
  if (direction === null) return null;
  const positive = direction === 'up';
  const Icon = positive ? ArrowUpwardIcon : ArrowDownwardIcon;
  const color = positive ? '#243044' : '#D96B67';
  return (
    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25, color, fontSize: '0.8125rem', fontWeight: 600 }}>
      <Icon sx={{ fontSize: 15 }} />
      {label}
    </Box>
  );
}

function HeroBalanceCard({ balance, prevTotals, trend, loading }) {
  const prevBalance = prevTotals ? prevTotals.income - prevTotals.expense : null;
  const delta = prevBalance !== null ? balance - prevBalance : null;

  return (
    <Card sx={{ height: '100%', bgcolor: '#111827', color: '#FFFFFF', border: 'none' }}>
      <CardContent sx={{ p: '1.75rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 600, color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: '0.05em', mb: 1 }}>
          Available Balance
        </Typography>
        {loading ? (
          <Skeleton width={180} height={48} sx={{ bgcolor: 'rgba(255,255,255,0.15)' }} />
        ) : (
          <Typography sx={{ fontSize: '2.25rem', fontWeight: 700, lineHeight: 1.15, mb: 1 }}>{formatINR(balance)}</Typography>
        )}
        {delta !== null && (
          <DeltaBadgeLight direction={delta >= 0 ? 'up' : 'down'} label={`${formatINR(Math.abs(delta))} vs last month`} />
        )}
        <Box sx={{ mt: 'auto', pt: 2, mx: -1 }}>
          <Sparkline data={trend} dataKey="balance" color="#C7A66A" height={56} />
        </Box>
      </CardContent>
    </Card>
  );
}

function DeltaBadgeLight({ direction, label }) {
  const positive = direction === 'up';
  const Icon = positive ? ArrowUpwardIcon : ArrowDownwardIcon;
  return (
    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25, color: positive ? '#C7A66A' : '#E9A6A3', fontSize: '0.8125rem', fontWeight: 600 }}>
      <Icon sx={{ fontSize: 15 }} />
      {label}
    </Box>
  );
}

function MetricCard({ title, value, trendKey, trend, color, deltaPct, favorableWhenUp, loading }) {
  const direction = deltaPct === null ? null : deltaPct >= 0 ? 'up' : 'down';
  const favorable = direction === null ? null : favorableWhenUp ? direction === 'up' : direction === 'down';

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: '1.5rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 600, color: '#77736D', textTransform: 'uppercase', letterSpacing: '0.05em', mb: 1 }}>
          {title}
        </Typography>
        {loading ? (
          <Skeleton width={110} height={34} />
        ) : (
          <Typography sx={{ fontSize: '1.5rem', fontWeight: 700, color: '#20242C', lineHeight: 1.15, mb: 0.75 }}>{formatINR(value)}</Typography>
        )}
        {deltaPct !== null && (
          <DeltaBadge direction={favorable ? 'up' : 'down'} label={`${deltaPct >= 0 ? '+' : ''}${deltaPct.toFixed(1)}%`} />
        )}
        <Box sx={{ mt: 'auto', pt: 1, mx: -1 }}>
          <Sparkline data={trend} dataKey={trendKey} color={color} height={40} />
        </Box>
      </CardContent>
    </Card>
  );
}

export default function StatsCards({ summary, transactions = [], selectedUserId = 'All', activeMonth = '', loading }) {
  const stats = buildStats(summary, transactions, selectedUserId, activeMonth);
  const prevTotals = previousMonthTotals(summary, selectedUserId, activeMonth);

  const scopedTransactions = useMemo(
    () => (selectedUserId !== 'All' ? transactions.filter((item) => String(item.logged_by_id || '0') === String(selectedUserId)) : transactions),
    [transactions, selectedUserId],
  );
  const trend = useMemo(() => buildDailyTrend(scopedTransactions, 14), [scopedTransactions]);

  const incomeDeltaPct = prevTotals ? percentChange(stats.income, prevTotals.income) : null;
  const expenseDeltaPct = prevTotals ? percentChange(stats.expense, prevTotals.expense) : null;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <HeroBalanceCard balance={stats.balance} prevTotals={prevTotals} trend={trend} loading={loading} />
      </Grid>
      <Grid item xs={6} md={3}>
        <MetricCard title="Income" value={stats.income} trendKey="income" trend={trend} color="#243044" deltaPct={incomeDeltaPct} favorableWhenUp loading={loading} />
      </Grid>
      <Grid item xs={6} md={3}>
        <MetricCard title="Expense" value={stats.expense} trendKey="expense" trend={trend} color="#D96B67" deltaPct={expenseDeltaPct} favorableWhenUp={false} loading={loading} />
      </Grid>
      <Grid item xs={12}>
        <Card>
          <CardContent sx={{ p: '1rem 1.5rem', display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box sx={{ width: 36, height: 36, borderRadius: '10px', bgcolor: '#F0EBE2', color: '#111827', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <ReceiptLongIcon sx={{ fontSize: 19 }} />
            </Box>
            <Typography sx={{ fontSize: '0.875rem', color: '#77736D' }}>
              <Box component="span" sx={{ fontWeight: 700, color: '#20242C' }}>{stats.count}</Box> transaction{stats.count === 1 ? '' : 's'} {activeMonth ? `in ${activeMonth}` : 'recorded all time'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
