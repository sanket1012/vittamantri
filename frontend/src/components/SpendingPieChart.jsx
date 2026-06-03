import { useMemo, useState } from 'react';
import { Box, Button, ButtonGroup, Card, CardContent, Skeleton, Typography } from '@mui/material';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { getCategoryColor } from '../utils/categoryColors.js';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

export default function SpendingPieChart({ transactions = [], loading, selectedUser = 'All Users' }) {
  const [mode, setMode] = useState('category');

  const data = useMemo(() => {
    const totals = transactions
      .filter((item) => item.type === 'expense')
      .reduce((acc, item) => {
        const key = mode === 'subcategory' ? item.subcategory || 'Uncategorized' : item.category || 'Uncategorized';
        acc[key] = (acc[key] || 0) + Number(item.amount || 0);
        return acc;
      }, {});

    return Object.entries(totals)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [transactions, mode]);

  return (
    <Card variant="outlined" sx={{ borderRadius: '0.75rem', height: '100%' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #EAECF0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography sx={{ fontSize: '1.25rem', fontWeight: 600, color: '#101828' }}>Spending by Category</Typography>
          <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>{selectedUser}</Typography>
        </Box>
        <ButtonGroup size="small">
          <Button variant={mode === 'category' ? 'contained' : 'outlined'} onClick={() => setMode('category')}>Category</Button>
          <Button variant={mode === 'subcategory' ? 'contained' : 'outlined'} onClick={() => setMode('subcategory')}>Subcategory</Button>
        </ButtonGroup>
      </Box>
      <CardContent sx={{ p: 3 }}>
        {loading ? (
          <Skeleton variant="rounded" height={280} />
        ) : data.length ? (
          <>
            <Box sx={{ height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={96} paddingAngle={3}>
                    {data.map((entry) => (
                      <Cell key={entry.name} fill={getCategoryColor(entry.name)} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatINR(value)} />
                </PieChart>
              </ResponsiveContainer>
            </Box>
            <Box sx={{ display: 'grid', gap: 1, mt: 1 }}>
              {data.slice(0, 8).map((item) => (
                <Box key={item.name} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                    <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: getCategoryColor(item.name), flexShrink: 0 }} />
                    <Typography sx={{ fontSize: '0.875rem', color: '#344054', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</Typography>
                  </Box>
                  <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#101828' }}>{formatINR(item.value)}</Typography>
                </Box>
              ))}
            </Box>
          </>
        ) : (
          <Box sx={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#667085' }}>No expense data found</Box>
        )}
      </CardContent>
    </Card>
  );
}
