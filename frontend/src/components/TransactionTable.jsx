import { useMemo, useState } from 'react';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { Box, Button, Card, Chip, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, Skeleton, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, Typography } from '@mui/material';

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

export default function TransactionTable({ transactions = [], loading, onDelete }) {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [sortNewest, setSortNewest] = useState(true);
  const [confirmRow, setConfirmRow] = useState(null);

  const sortedRows = useMemo(() => {
    return [...transactions].sort((a, b) => {
      const aStamp = `${a.date || ''} ${a.time || ''}`;
      const bStamp = `${b.date || ''} ${b.time || ''}`;
      return sortNewest ? bStamp.localeCompare(aStamp) : aStamp.localeCompare(bStamp);
    });
  }, [transactions, sortNewest]);

  const pageRows = sortedRows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const confirmDelete = async () => {
    if (!confirmRow) return;
    await onDelete(confirmRow.id);
    setConfirmRow(null);
  };

  return (
    <Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #EAECF0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#101828' }}>Transactions</Typography>
        <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>{sortedRows.length} records</Typography>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <Button variant="text" size="small" endIcon={sortNewest ? <KeyboardArrowDownIcon /> : <KeyboardArrowUpIcon />} onClick={() => setSortNewest((value) => !value)} sx={{ height: 28, p: 0, color: '#475467' }}>
                  Date
                </Button>
              </TableCell>
              <TableCell>User</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Source</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Type</TableCell>
              <TableCell align="center">Delete</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              Array.from({ length: 6 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell colSpan={8}><Skeleton height={42} /></TableCell>
                </TableRow>
              ))
            ) : pageRows.length ? (
              pageRows.map((row) => {
                const isIncome = row.type === 'income';
                const color = userColor(row.logged_by_id);
                return (
                  <TableRow key={row.id}>
                    <TableCell>
                      <Typography sx={{ fontSize: '0.875rem', color: '#101828' }}>{formatDate(row.date)}</Typography>
                      <Typography sx={{ fontSize: 12, color: '#667085' }}>{row.time || ''}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={row.logged_by || 'Unknown'} size="small" sx={{ bgcolor: `${color}18`, color, border: `1px solid ${color}30` }} />
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#101828' }}>{row.category || '-'}</Typography>
                      {row.subcategory && <Chip label={row.subcategory} size="small" sx={{ mt: 0.5, height: 20, bgcolor: '#F2F4F7', color: '#475467', fontSize: 11 }} />}
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ color: '#344054', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{row.description || '-'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ color: '#667085' }}>{row.source || '-'}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography sx={{ fontWeight: 600, color: isIncome ? '#059669' : '#DC2626' }}>{isIncome ? '+' : '-'}{formatINR(row.amount)}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={isIncome ? 'INCOME' : 'EXPENSE'}
                        size="small"
                        sx={isIncome ? { bgcolor: '#ECFDF3', color: '#067647', border: '1px solid #ABEFC6' } : { bgcolor: '#FEF2F2', color: '#D92D20' }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <IconButton onClick={() => setConfirmRow(row)} sx={{ color: '#98A2B3', '&:hover': { color: '#DC2626', bgcolor: '#FEF2F2' } }}>
                        <DeleteOutlineIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={8}>
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

      <Box sx={{ px: 3, py: 2, borderTop: '1px solid #EAECF0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>
          Showing {Math.min(page * rowsPerPage + pageRows.length, sortedRows.length)} of {sortedRows.length}
        </Typography>
        <TablePagination
          component="div"
          count={sortedRows.length}
          page={page}
          onPageChange={(_, nextPage) => setPage(nextPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(Number(event.target.value));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 20, 50]}
        />
      </Box>

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
    </Card>
  );
}
