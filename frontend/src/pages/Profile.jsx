import { useEffect, useState } from 'react';
import {
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  TextField,
  Typography,
} from '@mui/material';
import toast from 'react-hot-toast';
import { changePassword, getMe, unlinkTelegram } from '../api/client.js';
import ConnectTelegram from '../components/ConnectTelegram.jsx';

const ROLE_COLOR = { admin: '#111827', member: '#77736D' };
const ROLE_BG = { admin: '#F0EBE2', member: '#E3DDD4' };

function Section({ title, children }) {
  return (
    <Box sx={{ bgcolor: '#FCFBF8', border: '1px solid #E3DDD4', borderRadius: 2, p: 3, mb: 3 }}>
      <Typography sx={{ fontWeight: 600, color: '#20242C', fontSize: '0.95rem', mb: 2 }}>{title}</Typography>
      {children}
    </Box>
  );
}

export default function Profile({ currentUser: initialUser }) {
  const [profile, setProfile] = useState(initialUser);
  const currentUser = profile || initialUser;

  const refreshProfile = async () => {
    try {
      const data = await getMe();
      setProfile(data);
    } catch {
      // keep showing whatever we already had
    }
  };

  useEffect(() => { refreshProfile(); }, []);

  const initials = currentUser?.display_name
    ? currentUser.display_name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : '?';

  // Telegram linking
  const [telegramSaving, setTelegramSaving] = useState(false);

  const handleUnlinkTelegram = async () => {
    setTelegramSaving(true);
    try {
      await unlinkTelegram();
      toast.success('Telegram account unlinked.');
      await refreshProfile();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Could not unlink Telegram account.');
    } finally {
      setTelegramSaving(false);
    }
  };

  // Change password
  const [pwForm, setPwForm] = useState({ newPassword: '', confirm: '' });
  const [pwError, setPwError] = useState('');
  const [pwSaving, setPwSaving] = useState(false);

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (pwForm.newPassword.length < 6) {
      setPwError('Password must be at least 6 characters.');
      return;
    }
    if (pwForm.newPassword !== pwForm.confirm) {
      setPwError('Passwords do not match.');
      return;
    }
    setPwSaving(true);
    setPwError('');
    try {
      await changePassword({ newPassword: pwForm.newPassword });
      toast.success('Password updated!');
      setPwForm({ newPassword: '', confirm: '' });
    } catch (err) {
      setPwError(err.response?.data?.error || 'Could not update password.');
    } finally {
      setPwSaving(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', px: 3, py: 4 }}>
      {/* Identity card */}
      <Section title="Account">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Avatar sx={{ width: 52, height: 52, bgcolor: ROLE_COLOR[currentUser?.role] || '#77736D', fontWeight: 700, fontSize: '1.1rem' }}>
            {initials}
          </Avatar>
          <Box>
            <Typography sx={{ fontWeight: 600, color: '#20242C' }}>{currentUser?.display_name}</Typography>
            <Typography sx={{ color: '#77736D', fontSize: '0.875rem' }}>@{currentUser?.username}</Typography>
          </Box>
          <Chip
            label={currentUser?.role}
            size="small"
            sx={{ ml: 'auto', bgcolor: ROLE_BG[currentUser?.role] || '#E3DDD4', color: ROLE_COLOR[currentUser?.role] || '#77736D', fontWeight: 600, fontSize: '0.7rem' }}
          />
        </Box>
        <Divider />
        <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
          <Box>
            <Typography sx={{ fontSize: '0.75rem', color: '#77736D', mb: 0.25 }}>Username</Typography>
            <Typography sx={{ fontWeight: 500, color: '#20242C' }}>{currentUser?.username}</Typography>
          </Box>
          <Box>
            <Typography sx={{ fontSize: '0.75rem', color: '#77736D', mb: 0.25 }}>Household</Typography>
            <Typography sx={{ fontWeight: 500, color: '#20242C' }}>#{currentUser?.household_id}</Typography>
          </Box>
        </Box>
      </Section>

      {/* Telegram linking */}
      <Section title="Telegram">
        {currentUser?.telegram_id ? (
          <Box>
            <Typography sx={{ color: '#77736D', fontSize: '0.875rem', mb: 1.5 }}>
              Linked to Telegram ID <strong>{currentUser.telegram_id}</strong>. Bot messages from this account are routed to your household.
            </Typography>
            <Button variant="outlined" color="error" onClick={handleUnlinkTelegram} disabled={telegramSaving}>
              {telegramSaving ? <CircularProgress size={18} color="inherit" /> : 'Unlink Telegram'}
            </Button>
          </Box>
        ) : (
          <>
            <Typography sx={{ color: '#77736D', fontSize: '0.875rem', mb: 1.5 }}>
              Connect your Telegram account so the bot routes messages to your household — one tap, no ID to look up.
            </Typography>
            <ConnectTelegram onLinked={refreshProfile} />
          </>
        )}
      </Section>

      {/* Change password */}
      <Section title="Change Password">
        <Box component="form" onSubmit={handleChangePassword} sx={{ display: 'grid', gap: 1.5 }}>
          <TextField
            size="small"
            type="password"
            label="New Password"
            value={pwForm.newPassword}
            onChange={(e) => { setPwForm((f) => ({ ...f, newPassword: e.target.value })); setPwError(''); }}
            helperText="Minimum 6 characters"
          />
          <TextField
            size="small"
            type="password"
            label="Confirm New Password"
            value={pwForm.confirm}
            onChange={(e) => { setPwForm((f) => ({ ...f, confirm: e.target.value })); setPwError(''); }}
            error={!!pwError}
            helperText={pwError || ' '}
          />
          <Button type="submit" variant="contained" disabled={pwSaving} sx={{ justifySelf: 'flex-start' }}>
            {pwSaving ? <CircularProgress size={18} color="inherit" /> : 'Update Password'}
          </Button>
        </Box>
      </Section>
    </Box>
  );
}
