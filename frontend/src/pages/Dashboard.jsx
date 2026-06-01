import { useEffect, useMemo, useState } from 'react';
import { Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Grid, Skeleton, Typography, useMediaQuery, useTheme } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import toast from 'react-hot-toast';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { cleanGarbage, csvExportUrl, deleteTransaction, fetchCategories, fetchSummary, fetchTransactions, getUsers } from '../api/client.js';
import AddTransaction from '../components/AddTransaction.jsx';
import FilterBar from '../components/FilterBar.jsx';
import Header from '../components/Header.jsx';
import MonthlyBarChart from '../components/MonthlyBarChart.jsx';
import Sidebar from '../components/Sidebar.jsx';
import SpendingPieChart from '../components/SpendingPieChart.jsx';
import StatsCards from '../components/StatsCards.jsx';
import TransactionTable from '../components/TransactionTable.jsx';

export const SUBCATEGORY_OPTIONS = {
  'Food & Dining': ['Delivery', 'Dining Out', 'Snacks', 'Beverages'],
  Groceries: ['Vegetables', 'Dairy', 'Household', 'Fruits'],
  Transport: ['Fuel', 'Cab', 'Auto', 'Public Transport', 'Parking'],
  Shopping: ['Clothes', 'Electronics', 'Home Decor', 'Beauty', 'Accessories'],
  'Health & Medical': ['Medicine', 'Doctor Visit', 'Lab Test', 'Insurance'],
  Entertainment: ['OTT', 'Movies', 'Events', 'Games'],
  'Utilities & Bills': ['Electricity', 'Internet', 'Gas', 'Water'],
  'Investment & SIP': ['Mutual Fund', 'Stocks', 'Gold', 'FD', 'PPF'],
  'EMI & Loans': ['Home Loan', 'Personal Loan', 'Credit Card', 'Vehicle Loan'],
};

const isGarbage = (item) => !item.date || !item.category || !item.type || !Number(item.amount || 0);

const PAGE_TITLES = {
  dashboard: 'Dashboard',
  transactions: 'Transactions',
  analytics: 'Analytics',
  export: 'Export',
};

const PAGE_CAPTIONS = {
  dashboard: 'Quick view of income, expense, balance, and recent patterns.',
  transactions: 'Review, filter, and manage every logged transaction.',
  analytics: 'Study category mix, monthly movement, and recent money trends.',
  export: 'Download a clean CSV copy of your finance records.',
};

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

function buildTrendData(transactions) {
  const today = new Date();
  const days = Array.from({ length: 14 }, (_, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() - (13 - index));
    const key = date.toISOString().slice(0, 10);
    return {
      key,
      label: date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
      income: 0,
      expense: 0,
      balance: 0,
    };
  });
  const byDate = Object.fromEntries(days.map((day) => [day.key, day]));
  transactions.forEach((item) => {
    const bucket = byDate[item.date];
    if (!bucket) return;
    if (item.type === 'income') bucket.income += Number(item.amount || 0);
    if (item.type === 'expense') bucket.expense += Number(item.amount || 0);
  });
  return days.map((day) => ({ ...day, balance: day.income - day.expense }));
}

function TrendPlot({ transactions, loading, selectedUser }) {
  const data = useMemo(() => buildTrendData(transactions), [transactions]);

  return (
    <Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #EAECF0' }}>
        <Typography sx={{ fontSize: '1.25rem', fontWeight: 600, color: '#101828' }}>14-Day Money Trend</Typography>
        <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>{selectedUser}</Typography>
      </Box>
      <CardContent sx={{ p: 3 }}>
        {loading ? (
          <Skeleton variant="rounded" height={320} />
        ) : (
          <Box sx={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid stroke="#EAECF0" vertical={false} />
                <XAxis dataKey="label" stroke="#667085" tickLine={false} axisLine={false} />
                <YAxis stroke="#667085" tickLine={false} axisLine={false} tickFormatter={(value) => `₹${Number(value) / 1000}k`} />
                <Tooltip formatter={(value) => formatINR(value)} />
                <Legend />
                <Line type="monotone" dataKey="income" name="Income" stroke="#059669" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="expense" name="Expense" stroke="#DC2626" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="balance" name="Daily Balance" stroke="#004EEB" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

function ExportView({ onExport, transactions, selectedUser }) {
  const income = transactions.filter((item) => item.type === 'income').reduce((sum, item) => sum + Number(item.amount || 0), 0);
  const expense = transactions.filter((item) => item.type === 'expense').reduce((sum, item) => sum + Number(item.amount || 0), 0);

  return (
    <Box sx={{ display: 'grid', gap: 2 }}>
      <Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <Box>
              <Typography sx={{ fontSize: '1.25rem', fontWeight: 600, color: '#101828' }}>Export Transactions</Typography>
              <Typography sx={{ mt: 0.5, fontSize: '0.875rem', color: '#667085' }}>
                Download the complete CSV file for {selectedUser}. It includes date, user, category, source, and raw input.
              </Typography>
            </Box>
            <Button variant="contained" startIcon={<DownloadIcon />} onClick={onExport}>
              Download CSV
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography sx={{ color: '#475467', fontWeight: 600, textTransform: 'uppercase', fontSize: '0.857rem' }}>Records Ready</Typography>
              <Typography sx={{ mt: 1, fontSize: '1.714rem', fontWeight: 700, color: '#101828' }}>{transactions.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography sx={{ color: '#475467', fontWeight: 600, textTransform: 'uppercase', fontSize: '0.857rem' }}>Income</Typography>
              <Typography sx={{ mt: 1, fontSize: '1.714rem', fontWeight: 700, color: '#059669' }}>{formatINR(income)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography sx={{ color: '#475467', fontWeight: 600, textTransform: 'uppercase', fontSize: '0.857rem' }}>Expense</Typography>
              <Typography sx={{ mt: 1, fontSize: '1.714rem', fontWeight: 700, color: '#DC2626' }}>{formatINR(expense)}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default function Dashboard() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [cleanOpen, setCleanOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [filters, setFilters] = useState({ user: 'All', category: 'All', subcategory: 'All', type: 'All', month: '', search: '' });

  const loadData = async ({ quiet = false } = {}) => {
    if (!quiet) setLoading(true);
    try {
      const [transactionRows, summaryData, categoryRows, userRows] = await Promise.all([
        fetchTransactions(filters.month),
        fetchSummary(),
        fetchCategories(),
        getUsers(),
      ]);
      setTransactions(transactionRows);
      setSummary(summaryData);
      setCategories(categoryRows);
      setUsers(userRows);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Could not load dashboard data');
    } finally {
      if (!quiet) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters.month]);

  useEffect(() => {
    const timer = setInterval(() => loadData({ quiet: true }), 30000);
    return () => clearInterval(timer);
  }, [filters.month]);

  const selectedUserName = filters.user === 'All' ? 'All Users' : users.find((user) => String(user.logged_by_id) === String(filters.user))?.logged_by || 'Selected User';
  const invalidCount = transactions.filter(isGarbage).length;

  const filteredTransactions = useMemo(() => {
    const query = filters.search.trim().toLowerCase();
    return transactions.filter((item) => {
      const userMatch = filters.user === 'All' || String(item.logged_by_id || '0') === String(filters.user);
      const categoryMatch = filters.category === 'All' || item.category === filters.category;
      const subcategoryMatch = filters.subcategory === 'All' || item.subcategory === filters.subcategory;
      const typeMatch = filters.type === 'All' || item.type === filters.type.toLowerCase();
      const searchMatch = !query || `${item.description || ''} ${item.source || ''} ${item.logged_by || ''} ${item.id || ''}`.toLowerCase().includes(query);
      return userMatch && categoryMatch && subcategoryMatch && typeMatch && searchMatch;
    });
  }, [transactions, filters]);

  const handleDelete = async (id) => {
    try {
      await deleteTransaction(id);
      toast.success('Transaction deleted');
      await loadData();
    } catch (error) {
      toast.error('Could not delete. Try again.');
    }
  };

  const handleClean = async () => {
    try {
      const result = await cleanGarbage();
      toast.success(`Cleaned ${result.deleted_count} invalid transactions`);
      setCleanOpen(false);
      await loadData();
    } catch (error) {
      toast.error('Could not clean data. Try again.');
    }
  };

  const handleSaved = async () => {
    setAddOpen(false);
    await loadData();
  };

  const handleUserChange = (value) => {
    setFilters((current) => ({ ...current, user: value }));
  };

  const handleExport = () => {
    window.location.href = csvExportUrl;
  };

  const handleSidebarNavigate = (target) => {
    setActiveSection(target);
    setMobileOpen(false);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: '#F6F6F6' }}>
      <Sidebar userCount={users.length} mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} activeSection={activeSection} onNavigate={handleSidebarNavigate} />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Header
          title={PAGE_TITLES[activeSection] || 'Dashboard'}
          caption={PAGE_CAPTIONS[activeSection]}
          users={users}
          selectedUser={filters.user}
          onUserChange={handleUserChange}
          onMenuClick={() => setMobileOpen(true)}
          onExport={handleExport}
          onClean={() => setCleanOpen(true)}
          onAdd={() => setAddOpen(true)}
          invalidCount={invalidCount}
          showMenu={isMobile}
        />

        <Box sx={{ flex: 1, p: '20px', overflow: 'auto' }}>
          {activeSection === 'dashboard' && (
            <Box sx={{ display: 'grid', gap: 2 }}>
              <StatsCards summary={summary} transactions={transactions} selectedUserId={filters.user} activeMonth={filters.month} loading={loading} />
              <Grid container spacing={2}>
                <Grid item xs={12} md={5}>
                  <SpendingPieChart transactions={filteredTransactions} loading={loading} selectedUser={selectedUserName} />
                </Grid>
                <Grid item xs={12} md={7}>
                  <MonthlyBarChart transactions={filteredTransactions} loading={loading} selectedUser={selectedUserName} />
                </Grid>
              </Grid>
            </Box>
          )}

          {activeSection === 'transactions' && (
            <Box sx={{ display: 'grid', gap: 2 }}>
              <FilterBar filters={filters} setFilters={setFilters} categories={categories} users={users} subcategoryOptions={SUBCATEGORY_OPTIONS} transactions={transactions} />
              <TransactionTable transactions={filteredTransactions} loading={loading} onDelete={handleDelete} />
            </Box>
          )}

          {activeSection === 'analytics' && (
            <Box sx={{ display: 'grid', gap: 2 }}>
              <FilterBar filters={filters} setFilters={setFilters} categories={categories} users={users} subcategoryOptions={SUBCATEGORY_OPTIONS} transactions={transactions} />
              <TrendPlot transactions={filteredTransactions} loading={loading} selectedUser={selectedUserName} />
              <Grid container spacing={2}>
                <Grid item xs={12} md={5}>
                  <SpendingPieChart transactions={filteredTransactions} loading={loading} selectedUser={selectedUserName} />
                </Grid>
                <Grid item xs={12} md={7}>
                  <MonthlyBarChart transactions={filteredTransactions} loading={loading} selectedUser={selectedUserName} />
                </Grid>
              </Grid>
            </Box>
          )}

          {activeSection === 'export' && (
            <ExportView onExport={handleExport} transactions={filteredTransactions} selectedUser={selectedUserName} />
          )}
        </Box>
      </Box>

      <AddTransaction open={addOpen} onClose={() => setAddOpen(false)} onSaved={handleSaved} categories={categories} subcategoryOptions={SUBCATEGORY_OPTIONS} />

      <Dialog open={cleanOpen} onClose={() => setCleanOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 600, color: '#101828' }}>🧹 Clean Invalid Transactions</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2 }}>
          <Typography sx={{ color: '#344054' }}>
            This will permanently remove all transactions with missing amount, zero value, or empty category. This cannot be undone.
          </Typography>
          <Chip label={`${invalidCount} invalid transactions found`} sx={{ justifySelf: 'flex-start', bgcolor: '#FFFBEB', color: '#B54708' }} />
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button variant="outlined" onClick={() => setCleanOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleClean}>Clean Now</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
