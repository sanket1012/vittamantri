import { useEffect, useState } from 'react';
import CloseIcon from '@mui/icons-material/Close';
import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, IconButton, InputAdornment, MenuItem, Radio, RadioGroup, TextField, Typography } from '@mui/material';
import toast from 'react-hot-toast';
import { updateTransaction } from '../api/client.js';

export default function EditTransactionModal({ open, transaction, onClose, onSaved, categoriesFull = [] }) {
  const [form, setForm] = useState({
    amount: '',
    type: 'expense',
    category: '',
    subcategory: '',
    description: '',
    source: '',
    date: '',
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (transaction) {
      setForm({
        amount: transaction.amount ?? '',
        type: transaction.type ?? 'expense',
        category: transaction.category ?? '',
        subcategory: transaction.subcategory ?? '',
        description: transaction.description ?? '',
        source: transaction.source ?? '',
        date: transaction.date ? transaction.date.slice(0, 10) : '',
      });
    }
  }, [transaction]);

  const updateField = (key, value) => {
    setForm((current) => ({
      ...current,
      [key]: value,
      ...(key === 'category' ? { subcategory: '' } : {}),
    }));
  };

  const selectedCategory = categoriesFull.find((c) => c.name === form.category);
  const subcategories = selectedCategory?.subcategories ?? [];

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!form.amount || !form.category) {
      toast.error('Amount and category are required');
      return;
    }

    setSaving(true);
    try {
      await updateTransaction(transaction.id, {
        ...form,
        amount: Number(form.amount),
        subcategory: form.subcategory || null,
        source: form.source || null,
      });
      toast.success('Transaction updated');
      onSaved();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Could not update transaction');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogTitle sx={{ px: 3, py: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography sx={{ fontSize: '1.25rem', fontWeight: 600, color: '#101828' }}>Edit Transaction</Typography>
          <IconButton onClick={onClose} sx={{ color: '#98A2B3' }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent dividers sx={{ p: 3, display: 'grid', gap: 2 }}>
          <TextField
            required
            size="small"
            label="Amount"
            type="number"
            value={form.amount}
            onChange={(event) => updateField('amount', event.target.value)}
            InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }}
          />

          <RadioGroup row value={form.type} onChange={(event) => updateField('type', event.target.value)}>
            <FormControlLabel value="expense" control={<Radio />} label="Expense" />
            <FormControlLabel value="income" control={<Radio />} label="Income" />
          </RadioGroup>

          <TextField
            required
            select
            size="small"
            label="Category"
            value={form.category}
            onChange={(event) => updateField('category', event.target.value)}
          >
            {categoriesFull.map((category) => (
              <MenuItem key={category.name} value={category.name}>
                {category.emoji} {category.name}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            size="small"
            label="Subcategory"
            value={form.subcategory}
            onChange={(event) => updateField('subcategory', event.target.value)}
          >
            <MenuItem value="">None</MenuItem>
            {subcategories.map((subcategory) => (
              <MenuItem key={subcategory} value={subcategory}>
                {subcategory}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            size="small"
            label="Description"
            value={form.description}
            onChange={(event) => updateField('description', event.target.value)}
          />

          <TextField
            size="small"
            label="Source"
            placeholder="Zomato / Person name"
            value={form.source}
            onChange={(event) => updateField('source', event.target.value)}
          />

          <TextField
            size="small"
            label="Date"
            type="date"
            value={form.date}
            onChange={(event) => updateField('date', event.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </DialogContent>

        <DialogActions sx={{ p: 3 }}>
          <Button variant="outlined" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
}
