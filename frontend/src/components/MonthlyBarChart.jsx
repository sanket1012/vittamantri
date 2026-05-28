import { useMemo } from 'react';
import { Box, Card, CardContent, Skeleton, Typography } from '@mui/material';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

const monthKey = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

const monthLabel = (key) => {
  const [year, month] = key.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString('en-IN', { month: 'short' });
};

export default function MonthlyBarChart({ transactions = [], loading, selectedUser = 'All Users' }) {
  const data = useMemo(() => {
    const now = new Date();
    const keys = Array.from({ length: 6 }, (_, index) => {
      const date = new Date(now.getFullYear(), now.getMonth() - (5 - index), 1);
      return monthKey(date);
    });

    const totals = Object.fromEntries(keys.map((key) => [key, { month: monthLabel(key), income: 0, expense: 0 }]));
    transactions.forEach((item) => {
      const key = (item.date || '').slice(0, 7);
      if (!totals[key]) return;
      if (item.type === 'income') totals[key].income += Number(item.amount || 0);
      if (item.type === 'expense') totals[key].expense += Number(item.amount || 0);
    });
    return keys.map((key) => totals[key]);
  }, [transactions]);

  const currentMonth = new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });

  return (
    <Card variant="outlined" sx={{ borderRadius: '0.75rem', height: '100%' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #EAECF0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
        <Box>
          <Typography sx={{ fontSize: '1.25rem', fontWeight: 600, color: '#101828' }}>Monthly Overview</Typography>
          <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>{selectedUser}</Typography>
        </Box>
        <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>{currentMonth}</Typography>
      </Box>
      <CardContent sx={{ p: 3 }}>
        {loading ? (
          <Skeleton variant="rounded" height={320} />
        ) : (
          <Box sx={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid stroke="#EAECF0" vertical={false} />
                <XAxis dataKey="month" stroke="#667085" tickLine={false} axisLine={false} />
                <YAxis stroke="#667085" tickLine={false} axisLine={false} tickFormatter={(value) => `₹${Number(value) / 1000}k`} />
                <Tooltip formatter={(value) => formatINR(value)} cursor={{ fill: '#F9FAFB' }} />
                <Legend />
                <Bar dataKey="income" name="Income" fill="#059669" radius={[6, 6, 0, 0]} />
                <Bar dataKey="expense" name="Expense" fill="#DC2626" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
