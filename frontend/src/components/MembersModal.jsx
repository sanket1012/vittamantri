import { useEffect, useState } from 'react';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import KeyIcon from '@mui/icons-material/Key';
import {
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  MenuItem,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import toast from 'react-hot-toast';
import { addMember, deleteMember, getMembers, resetMemberPassword } from '../api/client.js';

const ROLE_COLORS = { admin: '#004EEB', member: '#344054' };
const ROLE_BG = { admin: '#EFF4FF', member: '#F2F4F7' };

function MemberRow({ member, currentUserId, onDeleted, onPasswordReset }) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [saving, setSaving] = useState(false);

  const initials = member.display_name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2);
  const isSelf = member.id === currentUserId;

  const handleDelete = async () => {
    setSaving(true);
    try {
      await deleteMember(member.id);
      toast.success(`${member.display_name} removed`);
      onDeleted(member.id);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Could not remove member');
    } finally {
      setSaving(false);
      setConfirmDelete(false);
    }
  };

  const handleResetPassword = async () => {
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setSaving(true);
    try {
      await resetMemberPassword(member.id, newPassword);
      toast.success('Password updated');
      setResetOpen(false);
      setNewPassword('');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Could not update password');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 1.25 }}>
      <Avatar sx={{ width: 36, height: 36, bgcolor: ROLE_COLORS[member.role] || '#344054', fontSize: '0.8rem', fontWeight: 700 }}>
        {initials}
      </Avatar>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography sx={{ fontWeight: 600, color: '#101828', fontSize: '0.875rem' }}>
          {member.display_name}
          {isSelf && <Typography component="span" sx={{ ml: 0.75, fontSize: '0.75rem', color: '#667085' }}>(you)</Typography>}
        </Typography>
        <Typography sx={{ fontSize: '0.75rem', color: '#667085' }}>@{member.username}</Typography>
      </Box>
      <Chip
        label={member.role}
        size="small"
        sx={{ bgcolor: ROLE_BG[member.role] || '#F2F4F7', color: ROLE_COLORS[member.role] || '#344054', fontWeight: 600, fontSize: '0.7rem', height: 22 }}
      />
      <Tooltip title="Reset password">
        <IconButton size="small" onClick={() => setResetOpen(true)} sx={{ color: '#667085' }}>
          <KeyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      {!isSelf && (
        <Tooltip title="Remove member">
          <IconButton size="small" onClick={() => setConfirmDelete(true)} sx={{ color: '#B54708' }}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}

      {/* Confirm delete dialog */}
      <Dialog open={confirmDelete} onClose={() => setConfirmDelete(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>Remove {member.display_name}?</DialogTitle>
        <DialogContent>
          <Typography sx={{ color: '#344054', fontSize: '0.875rem' }}>
            Their login will be removed. All their transactions remain in the household data.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button variant="outlined" onClick={() => setConfirmDelete(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete} disabled={saving}>
            {saving ? <CircularProgress size={18} color="inherit" /> : 'Remove'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset password dialog */}
      <Dialog open={resetOpen} onClose={() => { setResetOpen(false); setNewPassword(''); }} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>Reset password for {member.display_name}</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            fullWidth
            type="password"
            label="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            size="small"
            helperText="Minimum 6 characters"
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button variant="outlined" onClick={() => { setResetOpen(false); setNewPassword(''); }}>Cancel</Button>
          <Button variant="contained" onClick={handleResetPassword} disabled={saving}>
            {saving ? <CircularProgress size={18} color="inherit" /> : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default function MembersModal({ open, onClose, currentUser }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [addForm, setAddForm] = useState({ displayName: '', username: '', password: '', role: 'member' });
  const [addError, setAddError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    getMembers()
      .then(setMembers)
      .catch(() => toast.error('Could not load members'))
      .finally(() => setLoading(false));
  }, [open]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!addForm.username.trim() || !addForm.password) {
      setAddError('Username and password are required.');
      return;
    }
    setSaving(true);
    setAddError('');
    try {
      await addMember({
        username: addForm.username.trim(),
        displayName: addForm.displayName.trim() || addForm.username.trim(),
        password: addForm.password,
        role: addForm.role,
      });
      toast.success(`${addForm.displayName || addForm.username} added`);
      setAddForm({ displayName: '', username: '', password: '', role: 'member' });
      const updated = await getMembers();
      setMembers(updated);
    } catch (err) {
      setAddError(err.response?.data?.error || 'Could not add member');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleted = (id) => setMembers((prev) => prev.filter((m) => m.id !== id));

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 600, color: '#101828', borderBottom: '1px solid #EAECF0', pb: 2 }}>
        Family Members
        <Typography sx={{ fontSize: '0.875rem', color: '#667085', fontWeight: 400, mt: 0.25 }}>
          Manage who can log into VittaMantri
        </Typography>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {/* Existing members */}
        <Box sx={{ px: 3, pt: 2 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress size={28} />
            </Box>
          ) : members.length === 0 ? (
            <Typography sx={{ color: '#667085', fontSize: '0.875rem', py: 2 }}>No members yet.</Typography>
          ) : (
            members.map((m, i) => (
              <Box key={m.id}>
                <MemberRow member={m} currentUserId={currentUser?.id} onDeleted={handleDeleted} />
                {i < members.length - 1 && <Divider />}
              </Box>
            ))
          )}
        </Box>

        {/* Add member form */}
        <Box sx={{ px: 3, pt: 2, pb: 3, borderTop: '1px solid #EAECF0', mt: 2, bgcolor: '#F9FAFB' }}>
          <Typography sx={{ fontWeight: 600, color: '#344054', fontSize: '0.875rem', mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.75 }}>
            <AddIcon sx={{ fontSize: 16 }} /> Add Member
          </Typography>
          <Box component="form" onSubmit={handleAdd} sx={{ display: 'grid', gap: 1.5 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
              <TextField
                size="small"
                label="Display Name"
                placeholder="Vaishnavi"
                value={addForm.displayName}
                onChange={(e) => { setAddForm((f) => ({ ...f, displayName: e.target.value })); setAddError(''); }}
              />
              <TextField
                size="small"
                label="Username *"
                placeholder="vaishnavi"
                value={addForm.username}
                onChange={(e) => { setAddForm((f) => ({ ...f, username: e.target.value })); setAddError(''); }}
              />
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
              <TextField
                size="small"
                type="password"
                label="Password *"
                value={addForm.password}
                onChange={(e) => { setAddForm((f) => ({ ...f, password: e.target.value })); setAddError(''); }}
                helperText={addError || 'Min 6 characters'}
                error={!!addError}
              />
              <TextField
                select
                size="small"
                label="Role"
                value={addForm.role}
                onChange={(e) => setAddForm((f) => ({ ...f, role: e.target.value }))}
              >
                <MenuItem value="member">Member</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </TextField>
            </Box>
            <Button type="submit" variant="contained" disabled={saving} startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <AddIcon />} sx={{ justifySelf: 'flex-start' }}>
              {saving ? 'Adding…' : 'Add Member'}
            </Button>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid #EAECF0' }}>
        <Button variant="outlined" onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
