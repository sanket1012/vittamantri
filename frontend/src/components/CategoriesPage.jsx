import { useEffect, useState } from 'react';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import {
  Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent,
  DialogTitle, Grid, IconButton, Skeleton, TextField, Tooltip, Typography,
} from '@mui/material';
import toast from 'react-hot-toast';
import { addCategory, addSubcategory, deleteCategory, deleteSubcategory, fetchCategoriesFull } from '../api/client.js';
import { getCategoryColor } from '../utils/categoryColors.js';

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Add dialogs
  const [addCatOpen, setAddCatOpen] = useState(false);
  const [addSubOpen, setAddSubOpen] = useState(null);   // category name or null
  const [newCatName, setNewCatName] = useState('');
  const [newCatEmoji, setNewCatEmoji] = useState('');
  const [newSubName, setNewSubName] = useState('');

  // Delete confirmation
  const [confirmDeleteCat, setConfirmDeleteCat] = useState(null);    // category name or null
  const [confirmDeleteSub, setConfirmDeleteSub] = useState(null);    // {category, subcategory} or null

  const [saving, setSaving] = useState(false);

  const loadCategories = async () => {
    try {
      setLoading(true);
      setCategories(await fetchCategoriesFull());
    } catch {
      toast.error('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadCategories(); }, []);

  // ── Add category ───────────────────────────────────────────────────────────

  const handleAddCategorySubmit = async () => {
    if (!newCatName.trim()) { toast.error('Category name is required'); return; }
    setSaving(true);
    try {
      await addCategory({ name: newCatName.trim(), emoji: newCatEmoji.trim() || '🏷️' });
      toast.success('Category added');
      setAddCatOpen(false);
      setNewCatName(''); setNewCatEmoji('');
      await loadCategories();
    } catch { toast.error('Failed to add category'); }
    finally { setSaving(false); }
  };

  // ── Add subcategory ────────────────────────────────────────────────────────

  const handleAddSubSubmit = async () => {
    if (!newSubName.trim()) { toast.error('Subcategory name is required'); return; }
    setSaving(true);
    try {
      await addSubcategory(addSubOpen, newSubName.trim());
      toast.success('Subcategory added');
      setAddSubOpen(null); setNewSubName('');
      await loadCategories();
    } catch { toast.error('Failed to add subcategory'); }
    finally { setSaving(false); }
  };

  // ── Delete category ────────────────────────────────────────────────────────

  const handleDeleteCategoryConfirmed = async () => {
    setSaving(true);
    try {
      await deleteCategory(confirmDeleteCat);
      toast.success(`"${confirmDeleteCat}" deleted`);
      setConfirmDeleteCat(null);
      await loadCategories();
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Could not delete category');
    } finally { setSaving(false); }
  };

  // ── Delete subcategory ─────────────────────────────────────────────────────

  const handleDeleteSubConfirmed = async () => {
    const { category, subcategory } = confirmDeleteSub;
    setSaving(true);
    try {
      await deleteSubcategory(category, subcategory);
      toast.success(`"${subcategory}" removed`);
      setConfirmDeleteSub(null);
      await loadCategories();
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Could not delete subcategory');
    } finally { setSaving(false); }
  };

  return (
    <Box sx={{ display: 'grid', gap: 2 }}>
      {/* Top row */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography sx={{ fontSize: '0.875rem', color: '#667085' }}>
          {loading ? <Skeleton width={80} sx={{ display: 'inline-block' }} /> : `${categories.length} categories`}
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />}
          onClick={() => { setNewCatName(''); setNewCatEmoji(''); setAddCatOpen(true); }}>
          Add Category
        </Button>
      </Box>

      {/* Category grid */}
      {loading ? (
        <Grid container spacing={2}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={130} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Grid container spacing={2}>
          {categories.map((cat) => {
            const accent = getCategoryColor(cat.name);
            return (
              <Grid item xs={12} sm={6} md={4} key={cat.name}>
                <Card variant="outlined" sx={{ borderRadius: '0.75rem', borderTop: `3px solid ${accent}`, height: '100%' }}>
                  <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>

                    {/* Card header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', flex: 1, minWidth: 0 }}>
                        <Typography sx={{ fontSize: '1.4rem', lineHeight: 1 }}>{cat.emoji}</Typography>
                        <Typography sx={{ fontWeight: 700, color: '#101828', fontSize: '0.9rem' }}>{cat.name}</Typography>
                        {cat.is_custom && (
                          <Chip label="custom" size="small"
                            sx={{ height: 18, fontSize: '0.68rem', bgcolor: '#EFF6FF', color: '#004EEB', fontWeight: 600 }} />
                        )}
                      </Box>

                      {/* Action buttons */}
                      <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
                        <Tooltip title="Add subcategory">
                          <IconButton size="small"
                            onClick={() => { setNewSubName(''); setAddSubOpen(cat.name); }}
                            sx={{ color: '#667085', border: '1px solid #EAECF0', borderRadius: '6px', p: '3px',
                              '&:hover': { bgcolor: '#F2F4F7', color: '#344054' } }}>
                            <AddIcon sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>

                        <Tooltip title="Delete category">
                          <IconButton size="small"
                            onClick={() => setConfirmDeleteCat(cat.name)}
                            sx={{ color: '#98A2B3', border: '1px solid #EAECF0', borderRadius: '6px', p: '3px',
                              '&:hover': { color: '#DC2626', bgcolor: '#FEF2F2', borderColor: '#FCA5A5' } }}>
                            <DeleteOutlineIcon sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>

                    {/* Subcategory chips */}
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                      {cat.subcategories.length > 0 ? cat.subcategories.map((sub) => {
                        const isCustomSub = cat.custom_subcategories?.includes(sub);
                        return isCustomSub ? (
                          <Chip key={sub} label={sub} size="small"
                            onDelete={() => setConfirmDeleteSub({ category: cat.name, subcategory: sub })}
                            sx={{ bgcolor: `${accent}15`, color: accent, border: `1px solid ${accent}35`,
                                  fontSize: '0.72rem', height: 22,
                              '& .MuiChip-deleteIcon': { fontSize: 14, color: `${accent}80`, '&:hover': { color: '#DC2626' } } }} />
                        ) : (
                          <Chip key={sub} label={sub} size="small"
                            sx={{ bgcolor: `${accent}0D`, color: accent, border: `1px solid ${accent}22`,
                                  fontSize: '0.72rem', height: 22 }} />
                        );
                      }) : (
                        <Typography sx={{ fontSize: '0.8rem', color: '#98A2B3', fontStyle: 'italic' }}>
                          No subcategories
                        </Typography>
                      )}
                    </Box>

                    {/* Legend for custom subcategories */}
                    {cat.custom_subcategories?.length > 0 && (
                      <Typography sx={{ mt: 1, fontSize: '0.7rem', color: '#98A2B3' }}>
                        Darker border = custom (click × to remove)
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* ── Add Category dialog ──────────────────────────────────────────── */}
      <Dialog open={addCatOpen} onClose={() => setAddCatOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#101828' }}>Add Category</DialogTitle>
        <DialogContent sx={{ pt: '8px !important' }}>
          <Box sx={{ display: 'flex', gap: 1.5 }}>
            <TextField size="small" label="Emoji" value={newCatEmoji}
              onChange={(e) => setNewCatEmoji(e.target.value)}
              inputProps={{ maxLength: 2 }} sx={{ width: 80, flexShrink: 0 }}
              onKeyDown={(e) => e.key === 'Enter' && handleAddCategorySubmit()} />
            <TextField size="small" label="Category Name" value={newCatName} autoFocus fullWidth
              onChange={(e) => setNewCatName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddCategorySubmit()} />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button variant="outlined" onClick={() => setAddCatOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddCategorySubmit} disabled={!newCatName.trim() || saving}>
            {saving ? 'Adding…' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Add Subcategory dialog ───────────────────────────────────────── */}
      <Dialog open={Boolean(addSubOpen)} onClose={() => setAddSubOpen(null)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#101828' }}>Add Subcategory</DialogTitle>
        <DialogContent sx={{ pt: '4px !important' }}>
          <Typography sx={{ mb: 1.5, fontSize: '0.875rem', color: '#667085' }}>
            Adding to: <strong style={{ color: '#344054' }}>{addSubOpen}</strong>
          </Typography>
          <TextField size="small" label="Subcategory Name" value={newSubName} autoFocus fullWidth
            onChange={(e) => setNewSubName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddSubSubmit()} />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button variant="outlined" onClick={() => setAddSubOpen(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddSubSubmit} disabled={!newSubName.trim() || saving}>
            {saving ? 'Adding…' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Delete Category confirmation ─────────────────────────────────── */}
      <Dialog open={Boolean(confirmDeleteCat)} onClose={() => setConfirmDeleteCat(null)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#101828' }}>Delete category?</DialogTitle>
        <DialogContent>
          <Typography sx={{ color: '#344054' }}>
            Delete <strong>"{confirmDeleteCat}"</strong>? It will be removed from all dropdowns and the categories
            list. Existing transactions that use this category keep their value — you can reassign them via bulk edit.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button variant="outlined" onClick={() => setConfirmDeleteCat(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDeleteCategoryConfirmed} disabled={saving}>
            {saving ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Delete Subcategory confirmation ──────────────────────────────── */}
      <Dialog open={Boolean(confirmDeleteSub)} onClose={() => setConfirmDeleteSub(null)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#101828' }}>Remove subcategory?</DialogTitle>
        <DialogContent>
          <Typography sx={{ color: '#344054' }}>
            Remove <strong>"{confirmDeleteSub?.subcategory}"</strong> from{' '}
            <strong>"{confirmDeleteSub?.category}"</strong>? Transactions with this subcategory keep their value.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button variant="outlined" onClick={() => setConfirmDeleteSub(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDeleteSubConfirmed} disabled={saving}>
            {saving ? 'Removing…' : 'Remove'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
