import { useEffect, useState } from 'react';
import { Box, Button, CircularProgress, Paper, TextField, Typography } from '@mui/material';
import api, { getInvitePreview, registerUser } from '../api/client.js';
import BrandMark from '../components/BrandMark.jsx';

export default function AcceptInvite({ token, onJoined, onGoHome }) {
  const [status, setStatus] = useState('loading'); // loading | valid | invalid
  const [preview, setPreview] = useState(null);
  const [form, setForm] = useState({ displayName: '', username: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getInvitePreview(token)
      .then((data) => {
        setPreview(data);
        setForm((f) => ({ ...f, displayName: data.display_name || '' }));
        setStatus('valid');
      })
      .catch(() => setStatus('invalid'));
  }, [token]);

  const update = (field) => (e) => { setForm((f) => ({ ...f, [field]: e.target.value })); setError(''); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.username.trim() || !form.password) {
      setError('Username and password are required.');
      return;
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const data = await registerUser({
        username: form.username.trim(),
        displayName: form.displayName.trim(),
        password: form.password,
        inviteToken: token,
      });
      localStorage.setItem('jwt_token', data.token);
      api.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
      onJoined(data.user);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not join. The invite link may have expired.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#F7F3EA" px={2}>
      <Paper elevation={3} sx={{ p: 4, maxWidth: 420, width: '100%' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
          <BrandMark size={36} />
          <Typography variant="h5" fontWeight={600}>Samvitta</Typography>
        </Box>

        {status === 'loading' && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={28} />
          </Box>
        )}

        {status === 'invalid' && (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography sx={{ fontWeight: 600, color: '#20242C', mb: 1 }}>This invite link is invalid or has expired.</Typography>
            <Typography sx={{ color: '#77736D', fontSize: '0.875rem', mb: 3 }}>
              Ask whoever invited you to send a new link, or create your own household instead.
            </Typography>
            <Button variant="contained" onClick={onGoHome}>Go to Samvitta</Button>
          </Box>
        )}

        {status === 'valid' && (
          <>
            <Typography sx={{ color: '#77736D', fontSize: '0.9375rem', mb: 3 }}>
              <Box component="span" sx={{ fontWeight: 600, color: '#20242C' }}>{preview.inviter_name}</Box> invited you to join their household on Samvitta.
            </Typography>
            <Box component="form" onSubmit={handleSubmit}>
              <TextField fullWidth label="Display Name" value={form.displayName} onChange={update('displayName')} sx={{ mb: 2 }} />
              <TextField fullWidth label="Choose a username *" value={form.username} onChange={update('username')} autoFocus sx={{ mb: 2 }} />
              <TextField fullWidth type="password" label="Password *" value={form.password} onChange={update('password')} helperText="Minimum 6 characters" sx={{ mb: 2 }} />
              <TextField fullWidth type="password" label="Confirm Password *" value={form.confirm} onChange={update('confirm')} error={!!error} helperText={error || ' '} sx={{ mb: 2 }} />
              <Button type="submit" variant="contained" fullWidth disabled={submitting}>
                {submitting ? <CircularProgress size={22} color="inherit" /> : 'Join Household'}
              </Button>
            </Box>
          </>
        )}
      </Paper>
    </Box>
  );
}
