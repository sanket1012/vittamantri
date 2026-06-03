import { useMemo, useState } from 'react';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import {
  Box, Button, Card, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  IconButton, MenuItem, Select, Skeleton, Table, TableBody, TableCell, TableContainer,
  TableHead, TablePagination, TableRow, Tooltip, Typography,
} from '@mui/material';
import toast from 'react-hot-toast';
import { bulkUpdateTransactions } from '../api/client.js';
import { getCategoryColor } from '../utils/categoryColors.js';
import EditTransactionModal from './EditTransactionModal.jsx';

const USER_COLORS = ['#004EEB', '#7C3AED', '#059669', '#DC2626', '#F59E0B', '#0891B2', '#DB2777', '#65A30D'];

const formatINR = (amount = 0) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: Number(amount) % 1 === 0 ? 0 : 2 }).format(Number(amount || 0));

const userColor = (id = 0) => USER_COLORS[Math.abs(Number(id) || 0) % USER_COLORS.length];

const formatDate = (date) => {
  if (!date) return '-';
  const parsed = new Date(`${date}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
};

// ── Bulk-edit toolbar ─────────────────────────────────────────────────────────

function BulkEditBar({ selectedIds, categoriesFull, onApply, onClear }) {
  const [bulkCategory, setBulkCategory] = useState('');
  const [bulkSubcategory, setBulkSubcategory] = useState('');
  const [saving, setSaving] = useState(false);

  const subcategories = categoriesFull.find((c) => c.name === bulkCategory)?.subcategories || [];
  const count = selectedIds.size;

  const handleApply = async () => {
    if (!bulkCategory) { toast.error('Select a category first'); return; }
    setSaving(true);
    try {
      const fields = { category: bulkCategory };
      if (bulkSubcategory) fields.subcategory = bulkSubcategory;
      await bulkUpdateTransactions([...selectedIds], fields);
      toast.success(`Updated ${count} transaction${count > 1 ? 's' : ''}`);
      onApply();
      setBulkCategory('');
      setBulkSubcategory('');
    } catch {
      toast.error('Bulk update failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{
      mx: 3, my: 1.5, p: 2,
      bgcolor: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: '0.5rem',
      display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap',
    }}>
      <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#004EEB', minWidth: 110 }}>
        {count} selected
      </Typography>

      <Select
        size="small" displayEmpty value={bulkCategory}
        onChange={(e) => { setBulkCategory(e.target.value); setBulkSubcategory(''); }}
        sx={{ minWidth: 180, bgcolor: '#fff' }}
        renderValue={(v) => v || <span style={{ color: '#667085' }}>Set Category…</span>}
      >
        {categoriesFull.map((cat) => (
          <MenuItem key={cat.name} value={cat.name}>{cat.emoji} {cat.name}</MenuItem>
        ))}
      </Select>

      <Select
        size="small" displayEmpty value={bulkSubcategory}
        onChange={(e) => setBulkSubcategory(e.target.value)}
        disabled={!bulkCategory || subcategories.length === 0}
        sx={{ minWidth: 150, bgcolor: '#fff' }}
        renderValue={(v) => v || <span style={{ color: '#667085' }}>Subcategory…</span>}
      >
        <MenuItem value="">None</MenuItem>
        {subcategories.map((sub) => <MenuItem key={sub} value={sub}>{sub}</MenuItem>)}
      </Select>

      <Button variant="contained" size="small" onClick={handleApply} disabled={saving || !bulkCategory}
        sx={{ whiteSpace: 'nowrap' }}>
        {saving ? 'Applying…' : `Apply to ${count}`}
      </Button>

      <Button variant="outlined" size="small" onClick={onClear} sx={{ ml: 'auto', whiteSpace: 'nowrap' }}>
        Clear selection
      </Button>
    </Box>
  );
}

// ── Main table ────────────────────────────────────────────────────────────────

export default function TransactionTable({ transactions = [], loading, onDelete, onUpdated, categoriesFull = [] }) {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [sortNewest, setSortNewest] = useState(true);
  const [confirmRow, setConfirmRow] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());

  const sortedRows = useMemo(() => [...transactions].sort((a, b) => {
    const aStamp = `${a.date || ''} ${a.time || ''}`;
    const bStamp = `${b.date || ''} ${b.time || ''}`;
    return sortNewest ? bStamp.localeCompare(aStamp) : aStamp.localeCompare(bStamp);
  }), [transactions, sortNewest]);

  const pageRows = sortedRows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  const pageIds = pageRows.map((r) => r.id);
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id));
  const somePageSelected = pageIds.some((id) => selectedIds.has(id));

  const toggleRow = (id) => setSelectedIds((prev) => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });

  const toggleAllPage = () => {
    if (allPageSelected) {
      setSelectedIds((prev) => { const n = new Set(prev); pageIds.forEach((id) => n.delete(id)); return n; });
    } else {
      setSelectedIds((prev) => { const n = new Set(prev); pageIds.forEach((id) => n.add(id)); return n; });
    }
  };

  const clearSelection = () => setSelectedIds(new Set());

  const confirmDelete = async () => {
    if (!confirmRow) return;
    await onDelete(confirmRow.id);
    setConfirmRow(null);
    clearSelection();
  };

  return (
    <Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
      {/* Header */}
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #EAECF0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#101828' }}>Transactions</Typography>
        <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>{sortedRows.length} records</Typography>
      </Box>

      {/* Bulk-edit bar — visible when ≥1 row selected */}
      {selectedIds.size > 0 && (
        <BulkEditBar
          selectedIds={selectedIds}
          categoriesFull={categoriesFull}
          onApply={() => { clearSelection(); onUpdated?.(); }}
          onClear={clearSelection}
        />
      )}

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Tooltip title={allPageSelected ? 'Deselect page' : 'Select page'}>
                  <Checkbox
                    size="small"
                    indeterminate={somePageSelected && !allPageSelected}
                    checked={allPageSelected}
                    onChange={toggleAllPage}
                  />
                </Tooltip>
              </TableCell>
              <TableCell>
                <Button variant="text" size="small"
                  endIcon={sortNewest ? <KeyboardArrowDownIcon /> : <KeyboardArrowUpIcon />}
                  onClick={() => setSortNewest((v) => !v)}
                  sx={{ height: 28, p: 0, color: '#475467' }}>
                  Date
                </Button>
              </TableCell>
              <TableCell>User</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Source</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Type</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={9}><Skeleton height={42} /></TableCell>
                </TableRow>
              ))
            ) : pageRows.length ? (
              pageRows.map((row) => {
                const isIncome = row.type === 'income';
                const color = userColor(row.logged_by_id);
                const isSelected = selectedIds.has(row.id);
                return (
                  <TableRow key={row.id} selected={isSelected}
                    sx={{ '&.Mui-selected': { bgcolor: '#EFF6FF' }, '&.Mui-selected:hover': { bgcolor: '#DBEAFE' } }}>
                    <TableCell padding="checkbox">
                      <Checkbox size="small" checked={isSelected} onChange={() => toggleRow(row.id)} />
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ fontSize: '0.875rem', color: '#101828' }}>{formatDate(row.date)}</Typography>
                      <Typography sx={{ fontSize: 12, color: '#667085' }}>{row.time || ''}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={row.logged_by || 'Unknown'} size="small"
                        sx={{ bgcolor: `${color}18`, color, border: `1px solid ${color}30` }} />
                    </TableCell>
                    <TableCell>
                      {row.category ? (
                        <Chip label={row.category} size="small"
                          sx={{ bgcolor: `${getCategoryColor(row.category)}18`, color: getCategoryColor(row.category),
                                border: `1px solid ${getCategoryColor(row.category)}40`, fontWeight: 600, fontSize: '0.78rem' }} />
                      ) : (
                        <Typography sx={{ fontSize: '0.875rem', color: '#98A2B3' }}>-</Typography>
                      )}
                      {row.subcategory && (
                        <Chip label={row.subcategory} size="small"
                          sx={{ mt: 0.5, height: 20, bgcolor: `${getCategoryColor(row.category)}10`,
                                color: getCategoryColor(row.category), border: `1px solid ${getCategoryColor(row.category)}28`,
                                fontSize: 11 }} />
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ color: '#344054', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {row.description || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ color: '#667085' }}>{row.source || '-'}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography sx={{ fontWeight: 600, color: isIncome ? '#059669' : '#DC2626' }}>
                        {isIncome ? '+' : '-'}{formatINR(row.amount)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={isIncome ? 'INCOME' : 'EXPENSE'} size="small"
                        sx={isIncome
                          ? { bgcolor: '#ECFDF3', color: '#067647', border: '1px solid #ABEFC6' }
                          : { bgcolor: '#FEF2F2', color: '#D92D20' }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                        <Tooltip title="Edit transaction">
                          <IconButton size="small" onClick={() => setEditRow(row)}
                            sx={{ color: '#667085', '&:hover': { color: '#004EEB', bgcolor: '#EFF6FF' } }}>
                            <EditOutlinedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete transaction">
                          <IconButton size="small" onClick={() => setConfirmRow(row)}
                            sx={{ color: '#98A2B3', '&:hover': { color: '#DC2626', bgcolor: '#FEF2F2' } }}>
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={9}>
                  <Box sx={{ py: 7, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, color: '#667085' }}>
                    <Typography sx={{ fontSize: 42 }}>₹</Typography>
                    <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: '#344054' }}>No transactions found</Typography>
                    <Typography sx={{ fontSize: '0.875rem' }}>Try changing filters or add a new transaction.</Typography>
                  </Box>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Footer */}
      <Box sx={{ px: 3, py: 2, borderTop: '1px solid #EAECF0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>
          {selectedIds.size > 0 ? `${selectedIds.size} selected · ` : ''}
          Showing {Math.min(page * rowsPerPage + pageRows.length, sortedRows.length)} of {sortedRows.length}
        </Typography>
        <TablePagination
          component="div"
          count={sortedRows.length}
          page={page}
          onPageChange={(_, nextPage) => setPage(nextPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(Number(e.target.value)); setPage(0); }}
          rowsPerPageOptions={[10, 20, 50]}
        />
      </Box>

      {/* Delete confirm */}
      <Dialog open={Boolean(confirmRow)} onClose={() => setConfirmRow(null)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 600, color: '#101828' }}>Delete this transaction?</DialogTitle>
        <DialogContent>
          <Typography sx={{ color: '#344054' }}>
            {confirmRow ? `${formatINR(confirmRow.amount)} · ${confirmRow.category || '-'} · ${confirmRow.description || '-'}` : ''}
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button variant="outlined" onClick={() => setConfirmRow(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={confirmDelete}>Delete</Button>
        </DialogActions>
      </Dialog>

      {/* Single-row edit modal */}
      <EditTransactionModal
        open={Boolean(editRow)}
        transaction={editRow}
        onClose={() => setEditRow(null)}
        onSaved={() => { setEditRow(null); onUpdated?.(); }}
        categoriesFull={categoriesFull}
      />
    </Card>
  );
}
