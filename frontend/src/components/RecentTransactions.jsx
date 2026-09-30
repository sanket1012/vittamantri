import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import { Box, Button, Card, CardContent, Skeleton, Typography } from '@mui/material';
import { getCategoryColor } from '../utils/categoryColors.js';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
};

export default function RecentTransactions({ transactions = [], loading, onViewAll }) {
  const rows = [...transactions]
    .sort((a, b) => `${b.date || ''}${b.time || ''}`.localeCompare(`${a.date || ''}${a.time || ''}`))
    .slice(0, 5);

  return (
    <Card sx={{ height: '100%' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #E3DDD4', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#20242C' }}>Recent Transactions</Typography>
        {onViewAll && (
          <Button size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 16 }} />} onClick={onViewAll} sx={{ color: '#111827' }}>
            View all
          </Button>
        )}
      </Box>
      <CardContent sx={{ p: 3, display: 'grid', gap: 2 }}>
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} variant="rounded" height={40} />)
        ) : rows.length ? (
          rows.map((item) => (
            <Box key={item.id} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: getCategoryColor(item.category), flexShrink: 0 }} />
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography sx={{ fontSize: '0.875rem', fontWeight: 500, color: '#20242C', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.description || item.category || 'Transaction'}
                </Typography>
                <Typography sx={{ fontSize: '0.75rem', color: '#77736D' }}>{item.category}{item.source ? ` · ${item.source}` : ''}</Typography>
              </Box>
              <Box sx={{ textAlign: 'right', flexShrink: 0 }}>
                <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: item.type === 'income' ? '#243044' : '#D96B67' }}>
                  {item.type === 'income' ? '+' : '-'}{formatINR(item.amount)}
                </Typography>
                <Typography sx={{ fontSize: '0.75rem', color: '#77736D' }}>{formatDate(item.date)}</Typography>
              </Box>
            </Box>
          ))
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1, py: 3, textAlign: 'center' }}>
            <ReceiptLongIcon sx={{ fontSize: 28, color: '#77736D' }} />
            <Typography sx={{ fontSize: '0.875rem', color: '#77736D' }}>No transactions yet</Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
