import SearchIcon from '@mui/icons-material/Search';
import { Box, Button, Card, InputAdornment, MenuItem, TextField, Typography } from '@mui/material';

function InlineField({ label, children, minWidth = 160 }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth, flex: { xs: '1 1 100%', sm: '0 0 auto' } }}>
      <Typography sx={{ fontSize: '0.857rem', fontWeight: 500, color: '#344054', whiteSpace: 'nowrap' }}>{label}</Typography>
      {children}
    </Box>
  );
}

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

  return (
    <Card variant="outlined" sx={{ p: 2, borderRadius: '0.75rem', border: '1px solid #EAECF0' }}>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <InlineField label="User" minWidth={190}>
          <TextField select size="small" value={filters.user} onChange={(event) => updateFilter('user', event.target.value)} sx={{ minWidth: 140, flex: 1 }}>
            <MenuItem value="All">All Users</MenuItem>
            {users.map((user) => (
              <MenuItem key={user.logged_by_id} value={String(user.logged_by_id)}>
                {user.logged_by}
              </MenuItem>
            ))}
          </TextField>
        </InlineField>

        <InlineField label="Category" minWidth={250}>
          <TextField select size="small" value={filters.category} onChange={(event) => updateFilter('category', event.target.value)} sx={{ minWidth: 160, flex: 1 }}>
            <MenuItem value="All">All Categories</MenuItem>
            {categories.map((category) => (
              <MenuItem key={category.name} value={category.name}>
                {category.emoji} {category.name}
              </MenuItem>
            ))}
          </TextField>
        </InlineField>

        <InlineField label="Subcategory" minWidth={270}>
          <TextField select size="small" value={filters.subcategory} onChange={(event) => updateFilter('subcategory', event.target.value)} sx={{ minWidth: 160, flex: 1 }}>
            <MenuItem value="All">All Subcategories</MenuItem>
            {availableSubcategories.map((subcategory) => (
              <MenuItem key={subcategory} value={subcategory}>
                {subcategory}
              </MenuItem>
            ))}
          </TextField>
        </InlineField>

        <InlineField label="Type" minWidth={180}>
          <TextField select size="small" value={filters.type} onChange={(event) => updateFilter('type', event.target.value)} sx={{ minWidth: 120, flex: 1 }}>
            <MenuItem value="All">All Types</MenuItem>
            <MenuItem value="Income">Income</MenuItem>
            <MenuItem value="Expense">Expense</MenuItem>
          </TextField>
        </InlineField>

        <InlineField label="Month" minWidth={220}>
          <TextField size="small" type="month" value={filters.month} onChange={(event) => updateFilter('month', event.target.value)} sx={{ minWidth: 150, flex: 1 }} />
        </InlineField>

        <TextField
          size="small"
          placeholder="Search description, source, user..."
          value={filters.search}
          onChange={(event) => updateFilter('search', event.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon sx={{ color: '#98A2B3' }} /></InputAdornment> }}
          sx={{ minWidth: 240, flex: { xs: '1 1 100%', md: '1 1 240px' } }}
        />

        <Button variant="text" onClick={clearFilters}>
          Clear
        </Button>
      </Box>
    </Card>
  );
}
