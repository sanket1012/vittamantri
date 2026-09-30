import { useMemo } from 'react';
import { Box, Card, CardContent, Skeleton, Typography } from '@mui/material';
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { formatCompactINR } from '../utils/formatCurrency.js';
import { buildMonthlyTrend } from '../utils/trends.js';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

export default function MonthlyBarChart({ transactions = [], loading, selectedUser = 'All Users' }) {
  const data = useMemo(() => buildMonthlyTrend(transactions, 6), [transactions]);
  const currentMonth = new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });

  return (
    <Card sx={{ height: '100%' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #E3DDD4', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
        <Box>
          <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#20242C' }}>Cash Flow</Typography>
          <Typography sx={{ fontSize: '0.875rem', color: '#77736D' }}>{selectedUser}</Typography>
        </Box>
        <Typography sx={{ fontSize: '0.875rem', color: '#77736D' }}>{currentMonth}</Typography>
      </Box>
      <CardContent sx={{ p: 3 }}>
        {loading ? (
          <Skeleton variant="rounded" height={280} />
        ) : (
          <Box sx={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="cashflowIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#243044" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#243044" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="cashflowExpense" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D96B67" stopOpacity={0.22} />
                    <stop offset="100%" stopColor="#D96B67" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#E3DDD4" vertical={false} />
                <XAxis dataKey="month" stroke="#77736D" tickLine={false} axisLine={false} />
                <YAxis stroke="#77736D" tickLine={false} axisLine={false} width={64} tickFormatter={formatCompactINR} />
                <Tooltip formatter={(value) => formatINR(value)} contentStyle={{ borderRadius: 10, border: '1px solid #E3DDD4' }} />
                <Legend />
                <Area type="monotone" dataKey="income" name="Income" stroke="#243044" strokeWidth={2.5} fill="url(#cashflowIncome)" />
                <Area type="monotone" dataKey="expense" name="Expense" stroke="#D96B67" strokeWidth={2.5} fill="url(#cashflowExpense)" />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
