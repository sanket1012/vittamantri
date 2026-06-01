import { useEffect, useState } from 'react';
import AddIcon from '@mui/icons-material/Add';
import { Box, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Grid, IconButton, Skeleton, TextField, Typography, Button } from '@mui/material';
import toast from 'react-hot-toast';
import { addCategory, addSubcategory, fetchCategoriesFull } from '../api/client.js';

const USER_COLORS = ['#004EEB', '#7C3AED', '#059669', '#DC2626', '#D97706', '#0891B2'];

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addCatOpen, setAddCatOpen] = useState(false);
  const [addSubOpen, setAddSubOpen] = useState(null); // category name or null
  const [newCatName, setNewCatName] = useState('');
  const [newCatEmoji, setNewCatEmoji] = useState('');
  const [newSubName, setNewSubName] = useState('');
  const [saving, setSaving] = useState(false);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await fetchCategoriesFull();
      setCategories(data);
    } catch (err) {
      toast.error('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleAddCategoryOpen = () => {
    setNewCatName('');
    setNewCatEmoji('');
    setAddCatOpen(true);
  };

  const handleAddCategoryClose = () => {
    setAddCatOpen(false);
  };

  const handleAddCategorySubmit = async () => {
    if (!newCatName.trim()) {
      toast.error('Category name is required');
      return;
    }
    try {
      setSaving(true);
      await addCategory({ name: newCatName.trim(), emoji: newCatEmoji.trim() });
      toast.success('Category added');
      setAddCatOpen(false);
      await loadCategories();
    } catch (err) {
      toast.error('Failed to add category');
    } finally {
      setSaving(false);
    }
  };

  const handleAddSubOpen = (categoryName) => {
    setNewSubName('');
    setAddSubOpen(categoryName);
  };

  const handleAddSubClose = () => {
    setAddSubOpen(null);
  };

  const handleAddSubSubmit = async () => {
    if (!newSubName.trim()) {
      toast.error('Subcategory name is required');
      return;
    }
    try {
      setSaving(true);
      await addSubcategory(addSubOpen, newSubName.trim());
      toast.success('Subcategory added');
      setAddSubOpen(null);
      await loadCategories();
    } catch (err) {
      toast.error('Failed to add subcategory');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ p: 3, bgcolor: '#F6F6F6', minHeight: '100vh' }}>
      {/* Top row */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="body1" sx={{ color: '#344054', fontWeight: 500 }}>
          {loading ? (
            <Skeleton width={100} />
          ) : (
            `${categories.length} ${categories.length === 1 ? 'category' : 'categories'}`
          )}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddCategoryOpen}
          sx={{
            bgcolor: '#004EEB',
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: '8px',
            '&:hover': { bgcolor: '#0040C4' },
          }}
        >
          Add Category
        </Button>
      </Box>

      {/* Category cards grid */}
      {loading ? (
        <Grid container spacing={2}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={140} sx={{ borderRadius: '12px' }} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Grid container spacing={2}>
          {categories.map((cat, index) => {
            const accentColor = USER_COLORS[index % USER_COLORS.length];
            return (
              <Grid item xs={12} sm={6} md={4} key={cat.name}>
                <Card
                  elevation={0}
                  sx={{
                    borderRadius: '12px',
                    border: '1px solid #EAECF0',
                    borderTop: `3px solid ${accentColor}`,
                    bgcolor: '#FFFFFF',
                    height: '100%',
                  }}
                >
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    {/* Card header */}
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        {cat.emoji && (
                          <Typography variant="h6" component="span" lineHeight={1}>
                            {cat.emoji}
                          </Typography>
                        )}
                        <Typography
                          variant="body1"
                          sx={{ fontWeight: 700, color: '#101828' }}
                        >
                          {cat.name}
                        </Typography>
                        {cat.is_custom && (
                          <Chip
                            label="custom"
                            size="small"
                            sx={{
                              bgcolor: '#EFF4FF',
                              color: '#004EEB',
                              fontWeight: 600,
                              fontSize: '0.7rem',
                              height: 20,
                            }}
                          />
                        )}
                      </Box>
                      <IconButton
                        size="small"
                        onClick={() => handleAddSubOpen(cat.name)}
                        sx={{
                          color: '#667085',
                          border: '1px solid #EAECF0',
                          borderRadius: '6px',
                          p: '4px',
                          '&:hover': { bgcolor: '#F2F4F7', color: '#344054' },
                        }}
                      >
                        <AddIcon fontSize="small" />
                      </IconButton>
                    </Box>

                    {/* Subcategory chips */}
                    {cat.subcategories && cat.subcategories.length > 0 ? (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                        {cat.subcategories.map((sub) => (
                          <Chip
                            key={sub}
                            label={sub}
                            size="small"
                            sx={{
                              bgcolor: '#F2F4F7',
                              color: '#475467',
                              fontWeight: 500,
                              fontSize: '0.75rem',
                              height: 24,
                              borderRadius: '6px',
                            }}
                          />
                        ))}
                      </Box>
                    ) : (
                      <Typography
                        variant="body2"
                        sx={{ color: '#667085', fontStyle: 'italic' }}
                      >
                        No subcategories
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Add Category Dialog */}
      <Dialog
        open={addCatOpen}
        onClose={handleAddCategoryClose}
        maxWidth="xs"
        fullWidth
        PaperProps={{ sx: { borderRadius: '12px' } }}
      >
        <DialogTitle sx={{ color: '#101828', fontWeight: 700, pb: 1 }}>
          Add Category
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
            <TextField
              label="Emoji"
              value={newCatEmoji}
              onChange={(e) => setNewCatEmoji(e.target.value)}
              inputProps={{ maxLength: 2 }}
              sx={{ width: 80, flexShrink: 0 }}
              size="small"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddCategorySubmit();
              }}
            />
            <TextField
              label="Category Name"
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              fullWidth
              size="small"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddCategorySubmit();
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button
            onClick={handleAddCategoryClose}
            sx={{ color: '#344054', textTransform: 'none', fontWeight: 600 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleAddCategorySubmit}
            disabled={saving}
            sx={{
              bgcolor: '#004EEB',
              textTransform: 'none',
              fontWeight: 600,
              borderRadius: '8px',
              '&:hover': { bgcolor: '#0040C4' },
            }}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Subcategory Dialog */}
      <Dialog
        open={Boolean(addSubOpen)}
        onClose={handleAddSubClose}
        maxWidth="xs"
        fullWidth
        PaperProps={{ sx: { borderRadius: '12px' } }}
      >
        <DialogTitle sx={{ color: '#101828', fontWeight: 700, pb: 0.5 }}>
          Add Subcategory
        </DialogTitle>
        {addSubOpen && (
          <DialogContent sx={{ pt: 0.5 }}>
            <Typography variant="body2" sx={{ color: '#667085', mb: 2 }}>
              Adding to: <strong style={{ color: '#344054' }}>{addSubOpen}</strong>
            </Typography>
            <TextField
              label="Subcategory Name"
              value={newSubName}
              onChange={(e) => setNewSubName(e.target.value)}
              fullWidth
              size="small"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddSubSubmit();
              }}
            />
          </DialogContent>
        )}
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button
            onClick={handleAddSubClose}
            sx={{ color: '#344054', textTransform: 'none', fontWeight: 600 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleAddSubSubmit}
            disabled={saving}
            sx={{
              bgcolor: '#004EEB',
              textTransform: 'none',
              fontWeight: 600,
              borderRadius: '8px',
              '&:hover': { bgcolor: '#0040C4' },
            }}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
