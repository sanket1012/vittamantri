import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { Box, Card, CardContent, Grid, Skeleton, Typography } from '@mui/material';

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2,
  }).format(Number(amount || 0));

function buildStats(summary, transactions, selectedUserId) {
  if (selectedUserId !== 'All') {
    const rows = transactions.filter((item) => String(item.logged_by_id || '0') === String(selectedUserId));
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

function StatCard({ title, value, helper, color, icon, loading }) {
  return (
    <Card
      variant="outlined"
      sx={{
        borderRadius: '0.75rem',
        border: '1px solid #EAECF0',
        boxShadow: '0px 1px 2px 0px rgba(16,24,40,0.05)',
        borderTop: `3px solid ${color}`,
        height: '100%',
      }}
    >
      <CardContent sx={{ p: '1.71rem', '&:last-child': { pb: '1.71rem' } }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ fontSize: '0.857rem', fontWeight: 500, color: '#475467', textTransform: 'uppercase', letterSpacing: '0.05em', mb: 1 }}>
              {title}
            </Typography>
            {loading ? (
              <Skeleton width={130} height={36} />
            ) : (
              <Typography sx={{ fontSize: '1.714rem', fontWeight: 700, color: '#101828', wordBreak: 'break-word' }}>{value}</Typography>
            )}
            <Typography sx={{ fontSize: '0.857rem', color: '#667085', mt: 0.5 }}>{helper}</Typography>
          </Box>
          <Box sx={{ width: 44, height: 44, borderRadius: '10px', backgroundColor: `${color}10`, color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function StatsCards({ summary, transactions = [], selectedUserId = 'All', loading }) {
  const stats = buildStats(summary, transactions, selectedUserId);
  const balanceColor = stats.balance >= 0 ? '#004EEB' : '#DC2626';

  const cards = [
    { title: 'Total Income', value: formatINR(stats.income), helper: 'All time earnings', color: '#059669', icon: <TrendingUpIcon /> },
    { title: 'Total Expense', value: formatINR(stats.expense), helper: 'All time spending', color: '#DC2626', icon: <TrendingDownIcon /> },
    { title: 'Net Balance', value: formatINR(stats.balance), helper: 'Income minus expense', color: balanceColor, icon: <AccountBalanceWalletIcon /> },
    { title: 'Transactions', value: String(stats.count), helper: 'Total records', color: '#7C3AED', icon: <ReceiptLongIcon /> },
  ];

  return (
    <Grid container spacing={2}>
      {cards.map((card) => (
        <Grid item xs={12} sm={6} md={3} key={card.title}>
          <StatCard {...card} loading={loading} />
        </Grid>
      ))}
    </Grid>
  );
}
