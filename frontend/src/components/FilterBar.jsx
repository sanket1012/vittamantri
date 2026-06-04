import SearchIcon from '@mui/icons-material/Search';
import { Box, Button, Card, InputAdornment, MenuItem, TextField } from '@mui/material';

export default function FilterBar({ filters, setFilters, categories = [], users = [], subcategoryOptions = {}, transactions = [] }) {
  const availableSubcategories = filters.category !== 'All'
    ? subcategoryOptions[filters.category] || [...new Set(transactions.filter((item) => item.category === filters.category).map((item) => item.subcategory).filter(Boolean))]
    : [...new Set(transactions.map((item) => item.subcategory).filter(Boolean))];

  const updateFilter = (key, value) => {
    setFilters((current) => ({
      ...current,
      [key]: value,
      ...(key === 'category' ? { subcategory: 'All' } : {}),
    }));
  };

  const clearFilters = () => {
    setFilters((current) => ({ ...current, category: 'All', subcategory: 'All', type: 'All', month: '', search: '' }));
  };

  const selectSx = { minWidth: 110 };

  return (
    <Card variant="outlined" sx={{ px: 2, py: 1, borderRadius: '0.75rem', border: '1px solid #EAECF0' }}>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField select size="small" label="User" value={filters.user}
          onChange={(e) => updateFilter('user', e.target.value)} sx={selectSx}>
          <MenuItem value="All">All</MenuItem>
          {users.map((u) => <MenuItem key={u.logged_by_id} value={String(u.logged_by_id)}>{u.logged_by}</MenuItem>)}
        </TextField>

        <TextField select size="small" label="Category" value={filters.category}
          onChange={(e) => updateFilter('category', e.target.value)} sx={{ minWidth: 140 }}>
          <MenuItem value="All">All</MenuItem>
          {categories.map((c) => <MenuItem key={c.name} value={c.name}>{c.emoji} {c.name}</MenuItem>)}
        </TextField>

        <TextField select size="small" label="Subcategory" value={filters.subcategory}
          onChange={(e) => updateFilter('subcategory', e.target.value)} sx={{ minWidth: 130 }}>
          <MenuItem value="All">All</MenuItem>
          {availableSubcategories.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
        </TextField>

        <TextField select size="small" label="Type" value={filters.type}
          onChange={(e) => updateFilter('type', e.target.value)} sx={selectSx}>
          <MenuItem value="All">All</MenuItem>
          <MenuItem value="Income">Income</MenuItem>
          <MenuItem value="Expense">Expense</MenuItem>
        </TextField>

        <TextField size="small" type="month" label="Month" value={filters.month}
          onChange={(e) => updateFilter('month', e.target.value)}
          InputLabelProps={{ shrink: true }} sx={{ minWidth: 140 }} />

        <TextField size="small" placeholder="Search…" value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon sx={{ fontSize: 16, color: '#98A2B3' }} /></InputAdornment> }}
          sx={{ minWidth: 180, flex: '1 1 180px' }} />

        <Button variant="text" size="small" onClick={clearFilters} sx={{ whiteSpace: 'nowrap', color: '#667085' }}>
          Clear
        </Button>
      </Box>
    </Card>
  );
}
