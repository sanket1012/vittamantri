import { useCallback, useEffect, useMemo, useState } from 'react';
import AddIcon from '@mui/icons-material/Add';
import DonutLargeIcon from '@mui/icons-material/DonutLarge';
import { Box, Button, ButtonGroup, Card, CardContent, Skeleton, Typography } from '@mui/material';
import { Cell, Pie, PieChart, Tooltip } from 'recharts';
import { getCategoryColor } from '../utils/categoryColors.js';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

// Recharts' Pie needs a real pixel width/height to compute its radius, and
// ResponsiveContainer can miss the container's true size on first paint
// inside a Grid layout (the donut would render as a tiny clipped sliver).
// Measuring directly with ResizeObserver sidesteps that race entirely.
//
// The measured Box only exists once loading/empty-state branches resolve, so
// a plain useRef + useEffect(fn, []) would find ref.current still null on
// that first effect run and never retry. A callback ref re-fires whenever
// the DOM node actually mounts, so the observer always attaches to the real
// element once it exists.
function useContainerSize() {
  const [node, setNode] = useState(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const ref = useCallback((el) => setNode(el), []);

  useEffect(() => {
    if (!node) return undefined;
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ width, height });
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [node]);

  return [ref, size];
}

export default function SpendingPieChart({ transactions = [], loading, selectedUser = 'All Users', onAddExpense }) {
  const [mode, setMode] = useState('category');
  const [containerRef, { width, height }] = useContainerSize();

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

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const chartSize = Math.max(0, Math.min(width || 0, height || 0));
  const outerRadius = chartSize ? chartSize / 2 - 4 : 0;
  const innerRadius = outerRadius * 0.62;

  return (
    <Card sx={{ height: '100%' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #E7E9E5', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#17211E' }}>Spending</Typography>
          <Typography sx={{ fontSize: '0.875rem', color: '#737B77' }}>{selectedUser}</Typography>
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
            <Box ref={containerRef} sx={{ position: 'relative', height: 220 }}>
              {chartSize > 0 && (
                <PieChart width={width} height={height}>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={innerRadius}
                    outerRadius={outerRadius}
                    paddingAngle={3}
                    isAnimationActive={false}
                  >
                    {data.map((entry) => (
                      <Cell key={entry.name} fill={getCategoryColor(entry.name)} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatINR(value)} />
                </PieChart>
              )}
              <Box sx={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                <Typography sx={{ fontSize: '1.25rem', fontWeight: 700, color: '#17211E' }}>{formatINR(total)}</Typography>
                <Typography sx={{ fontSize: '0.75rem', color: '#737B77' }}>spent</Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'grid', gap: 1, mt: 1 }}>
              {data.slice(0, 6).map((item) => {
                const pct = total ? ((item.value / total) * 100).toFixed(1) : 0;
                return (
                  <Box key={item.name} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                      <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: getCategoryColor(item.name), flexShrink: 0 }} />
                      <Typography sx={{ fontSize: '0.875rem', color: '#17211E', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
                      <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#17211E' }}>{formatINR(item.value)}</Typography>
                      <Typography sx={{ fontSize: '0.75rem', color: '#737B77', minWidth: 38, textAlign: 'right' }}>{pct}%</Typography>
                    </Box>
                  </Box>
                );
              })}
            </Box>
          </>
        ) : (
          <Box sx={{ height: 280, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1.5, textAlign: 'center' }}>
            <Box sx={{ width: 52, height: 52, borderRadius: '50%', bgcolor: '#F0F3F1', color: '#123F36', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <DonutLargeIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography sx={{ fontWeight: 600, color: '#17211E' }}>No spending yet</Typography>
            <Typography sx={{ fontSize: '0.875rem', color: '#737B77', maxWidth: 220 }}>
              Add your first expense to start seeing category insights.
            </Typography>
            {onAddExpense && (
              <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={onAddExpense} sx={{ mt: 0.5 }}>
                Add Expense
              </Button>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
