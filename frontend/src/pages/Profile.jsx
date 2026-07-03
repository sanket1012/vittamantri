import { useEffect, useState } from 'react';
import {
  Alert,
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
import { changePassword, getMe, linkTelegram, unlinkTelegram } from '../api/client.js';

const ROLE_COLOR = { admin: '#004EEB', member: '#344054' };
const ROLE_BG = { admin: '#EFF4FF', member: '#F2F4F7' };

function Section({ title, children }) {
  return (
    <Box sx={{ bgcolor: '#FFFFFF', border: '1px solid #EAECF0', borderRadius: 2, p: 3, mb: 3 }}>
      <Typography sx={{ fontWeight: 600, color: '#101828', fontSize: '0.95rem', mb: 2 }}>{title}</Typography>
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
  const [telegramId, setTelegramId] = useState('');
  const [telegramSaving, setTelegramSaving] = useState(false);

  const handleLinkTelegram = async (e) => {
    e.preventDefault();
    const id = parseInt(telegramId.trim(), 10);
    if (!id || isNaN(id)) {
      toast.error('Enter a valid Telegram ID (numeric).');
      return;
    }
    setTelegramSaving(true);
    try {
      await linkTelegram(id);
      toast.success('Telegram account linked!');
      setTelegramId('');
      await refreshProfile();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Could not link Telegram account.');
    } finally {
      setTelegramSaving(false);
    }
  };

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
      <Typography sx={{ fontWeight: 700, fontSize: '1.5rem', color: '#101828', mb: 3 }}>Profile</Typography>

      {/* Identity card */}
      <Section title="Account">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Avatar sx={{ width: 52, height: 52, bgcolor: ROLE_COLOR[currentUser?.role] || '#344054', fontWeight: 700, fontSize: '1.1rem' }}>
            {initials}
          </Avatar>
          <Box>
            <Typography sx={{ fontWeight: 600, color: '#101828' }}>{currentUser?.display_name}</Typography>
            <Typography sx={{ color: '#667085', fontSize: '0.875rem' }}>@{currentUser?.username}</Typography>
          </Box>
          <Chip
            label={currentUser?.role}
            size="small"
            sx={{ ml: 'auto', bgcolor: ROLE_BG[currentUser?.role] || '#F2F4F7', color: ROLE_COLOR[currentUser?.role] || '#344054', fontWeight: 600, fontSize: '0.7rem' }}
          />
        </Box>
        <Divider />
        <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
          <Box>
            <Typography sx={{ fontSize: '0.75rem', color: '#667085', mb: 0.25 }}>Username</Typography>
            <Typography sx={{ fontWeight: 500, color: '#101828' }}>{currentUser?.username}</Typography>
          </Box>
          <Box>
            <Typography sx={{ fontSize: '0.75rem', color: '#667085', mb: 0.25 }}>Household</Typography>
            <Typography sx={{ fontWeight: 500, color: '#101828' }}>#{currentUser?.household_id}</Typography>
          </Box>
        </Box>
      </Section>

      {/* Telegram linking */}
      <Section title="Telegram">
        {currentUser?.telegram_id ? (
          <Box>
            <Typography sx={{ color: '#344054', fontSize: '0.875rem', mb: 1.5 }}>
              Linked to Telegram ID <strong>{currentUser.telegram_id}</strong>. Bot messages from this account are routed to your household.
            </Typography>
            <Button variant="outlined" color="error" onClick={handleUnlinkTelegram} disabled={telegramSaving}>
              {telegramSaving ? <CircularProgress size={18} color="inherit" /> : 'Unlink Telegram'}
            </Button>
          </Box>
        ) : (
          <>
            <Typography sx={{ color: '#344054', fontSize: '0.875rem', mb: 1.5 }}>
              Link your Telegram account so the bot routes messages to your household.
              Send <code>/start</code> to the bot, then forward your Telegram user ID here.
            </Typography>
            <Alert severity="info" sx={{ mb: 2, fontSize: '0.8rem' }}>
              To find your Telegram ID: message <strong>@userinfobot</strong> on Telegram — it will reply with your numeric ID.
            </Alert>
            <Box component="form" onSubmit={handleLinkTelegram} sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
              <TextField
                size="small"
                label="Telegram User ID"
                placeholder="e.g. 5997163595"
                value={telegramId}
                onChange={(e) => setTelegramId(e.target.value)}
                sx={{ flex: 1 }}
              />
              <Button type="submit" variant="contained" disabled={telegramSaving} sx={{ mt: 0.25 }}>
                {telegramSaving ? <CircularProgress size={18} color="inherit" /> : 'Link'}
              </Button>
            </Box>
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
