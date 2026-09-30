import { useEffect, useState } from 'react';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import HourglassTopIcon from '@mui/icons-material/HourglassTop';
import KeyIcon from '@mui/icons-material/Key';
import TelegramIcon from '@mui/icons-material/Telegram';
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
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import toast from 'react-hot-toast';
import {
  addMember,
  cancelMemberInvite,
  createMemberInvite,
  deleteMember,
  getMemberInvites,
  getMembers,
  resetMemberPassword,
} from '../api/client.js';

const ROLE_COLORS = { admin: '#111827', member: '#77736D' };
const ROLE_BG = { admin: '#F0EBE2', member: '#F0EBE2' };

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
      <Avatar sx={{ width: 36, height: 36, bgcolor: ROLE_COLORS[member.role] || '#77736D', fontSize: '0.8rem', fontWeight: 700 }}>
        {initials}
      </Avatar>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography sx={{ fontWeight: 600, color: '#20242C', fontSize: '0.875rem' }}>
          {member.display_name}
          {isSelf && <Typography component="span" sx={{ ml: 0.75, fontSize: '0.75rem', color: '#77736D' }}>(you)</Typography>}
        </Typography>
        <Typography sx={{ fontSize: '0.75rem', color: '#77736D' }}>@{member.username}</Typography>
      </Box>
      <Chip
        label={member.role}
        size="small"
        sx={{ bgcolor: ROLE_BG[member.role] || '#F0EBE2', color: ROLE_COLORS[member.role] || '#77736D', fontWeight: 600, fontSize: '0.7rem', height: 22 }}
      />
      <Tooltip title="Reset password">
        <IconButton size="small" onClick={() => setResetOpen(true)} sx={{ color: '#77736D' }}>
          <KeyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      {!isSelf && (
        <Tooltip title="Remove member">
          <IconButton size="small" onClick={() => setConfirmDelete(true)} sx={{ color: '#A98252' }}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}

      {/* Confirm delete dialog */}
      <Dialog open={confirmDelete} onClose={() => setConfirmDelete(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>Remove {member.display_name}?</DialogTitle>
        <DialogContent>
          <Typography sx={{ color: '#77736D', fontSize: '0.875rem' }}>
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

function PendingInviteRow({ invite, onCancelled }) {
  const [cancelling, setCancelling] = useState(false);

  const handleCancel = async () => {
    setCancelling(true);
    try {
      await cancelMemberInvite(invite.id);
      onCancelled(invite.id);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Could not cancel invite');
      setCancelling(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 1 }}>
      <Box sx={{ width: 36, height: 36, borderRadius: '50%', bgcolor: '#F6EFE1', color: '#A98252', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <HourglassTopIcon sx={{ fontSize: 18 }} />
      </Box>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography sx={{ fontWeight: 600, color: '#20242C', fontSize: '0.875rem' }}>{invite.display_name}</Typography>
        <Typography sx={{ fontSize: '0.75rem', color: '#77736D' }}>{invite.phone_number} · invited {invite.created_at}</Typography>
      </Box>
      <Chip label="Pending" size="small" sx={{ bgcolor: '#F6EFE1', color: '#A98252', fontWeight: 600, fontSize: '0.7rem', height: 22 }} />
      <Tooltip title="Cancel invite">
        <IconButton size="small" onClick={handleCancel} disabled={cancelling} sx={{ color: '#A98252' }}>
          {cancelling ? <CircularProgress size={16} /> : <DeleteIcon fontSize="small" />}
        </IconButton>
      </Tooltip>
    </Box>
  );
}

function InviteByPhoneForm({ onInvited }) {
  const [form, setForm] = useState({ displayName: '', phoneNumber: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.displayName.trim() || !form.phoneNumber.trim()) {
      setError('Name and phone number are required.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const data = await createMemberInvite({ phoneNumber: form.phoneNumber.trim(), displayName: form.displayName.trim() });
      setResult(data);
      setForm({ displayName: '', phoneNumber: '' });
      onInvited();
    } catch (err) {
      setError(err.response?.data?.error || 'Could not create invite');
    } finally {
      setSaving(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.invite_link);
      toast.success('Link copied');
    } catch {
      toast.error('Could not copy link');
    }
  };

  return (
    <Box>
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 1.5 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
          <TextField
            size="small"
            label="Name"
            placeholder="Vaishnavi"
            value={form.displayName}
            onChange={(e) => { setForm((f) => ({ ...f, displayName: e.target.value })); setError(''); }}
          />
          <TextField
            size="small"
            label="Phone number"
            placeholder="+91 98765 43210"
            value={form.phoneNumber}
            onChange={(e) => { setForm((f) => ({ ...f, phoneNumber: e.target.value })); setError(''); }}
            error={!!error}
            helperText={error || 'Used for your records — not verified automatically'}
          />
        </Box>
        <Button type="submit" variant="contained" disabled={saving} startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <AddIcon />} sx={{ justifySelf: 'flex-start' }}>
          {saving ? 'Creating invite…' : 'Create Invite Link'}
        </Button>
      </Box>

      {result && (
        <Box sx={{ mt: 2, p: 2, borderRadius: '0.75rem', bgcolor: '#F0EBE2', border: '1px solid #E3DDD4' }}>
          <Typography sx={{ fontSize: '0.8125rem', fontWeight: 600, color: '#111827', mb: 1 }}>
            Invite ready — share it with them
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<TelegramIcon />}
              component="a"
              href={result.telegram_share_url}
              target="_blank"
              rel="noopener"
              sx={{ bgcolor: '#229ED9', '&:hover': { bgcolor: '#1b87ba' } }}
            >
              Share via Telegram
            </Button>
            <Button size="small" variant="outlined" startIcon={<ContentCopyIcon />} onClick={handleCopy}>
              Copy Link
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
}

export default function MembersModal({ open, onClose, currentUser }) {
  const [tab, setTab] = useState(0); // 0 = Invite by phone, 1 = Add directly
  const [members, setMembers] = useState([]);
  const [invites, setInvites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [addForm, setAddForm] = useState({ displayName: '', username: '', password: '', role: 'member' });
  const [addError, setAddError] = useState('');
  const [saving, setSaving] = useState(false);

  const loadInvites = () => getMemberInvites().then(setInvites).catch(() => {});

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    Promise.all([getMembers().then(setMembers), loadInvites()])
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
      <DialogTitle sx={{ fontWeight: 600, color: '#20242C', borderBottom: '1px solid #E3DDD4', pb: 2 }}>
        Family Members
        <Typography sx={{ fontSize: '0.875rem', color: '#77736D', fontWeight: 400, mt: 0.25 }}>
          Manage who can log into Samvitta
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
            <Typography sx={{ color: '#77736D', fontSize: '0.875rem', py: 2 }}>No members yet.</Typography>
          ) : (
            members.map((m, i) => (
              <Box key={m.id}>
                <MemberRow member={m} currentUserId={currentUser?.id} onDeleted={handleDeleted} />
                {i < members.length - 1 && <Divider />}
              </Box>
            ))
          )}
        </Box>

        {/* Pending invites */}
        {!loading && invites.length > 0 && (
          <Box sx={{ px: 3, pt: 1 }}>
            <Divider sx={{ my: 1.5 }} />
            <Typography sx={{ fontWeight: 600, color: '#77736D', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', mb: 0.5 }}>
              Pending Invites
            </Typography>
            {invites.map((inv, i) => (
              <Box key={inv.id}>
                <PendingInviteRow invite={inv} onCancelled={(id) => setInvites((prev) => prev.filter((x) => x.id !== id))} />
                {i < invites.length - 1 && <Divider />}
              </Box>
            ))}
          </Box>
        )}

        {/* Add / Invite member */}
        <Box sx={{ px: 3, pt: 1.5, pb: 3, borderTop: '1px solid #E3DDD4', mt: 2, bgcolor: '#F0EBE2' }}>
          <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2, minHeight: 36 }}>
            <Tab label="Invite by Phone" sx={{ minHeight: 36, py: 0.5 }} />
            <Tab label="Add Directly" sx={{ minHeight: 36, py: 0.5 }} />
          </Tabs>

          {tab === 0 ? (
            <InviteByPhoneForm onInvited={loadInvites} />
          ) : (
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
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid #E3DDD4' }}>
        <Button variant="outlined" onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
