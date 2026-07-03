import { useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  Paper,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import api, { registerUser } from '../api/client.js';

export default function LoginGate({ onUnlock }) {
  const [tab, setTab] = useState(0); // 0 = Sign In, 1 = Register
  const [form, setForm] = useState({ username: '', password: '', displayName: '', confirm: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) => { setForm((f) => ({ ...f, [field]: e.target.value })); setError(''); };

  const handleSignIn = async (e) => {
    e.preventDefault();
    if (!form.username.trim() || !form.password) {
      setError('Username and password are required.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/login', { username: form.username.trim(), password: form.password });
      localStorage.setItem('jwt_token', data.token);
      api.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
      onUnlock(data.user);
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
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
    setLoading(true);
    setError('');
    try {
      const data = await registerUser({
        username: form.username.trim(),
        displayName: form.displayName.trim(),
        password: form.password,
      });
      localStorage.setItem('jwt_token', data.token);
      api.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
      onUnlock(data.user);
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Try a different username.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#f5f5f5">
      <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h5" fontWeight={600} mb={0.5}>वित्तमंत्री</Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>Family Finance Tracker</Typography>

        <Tabs value={tab} onChange={(_, v) => { setTab(v); setForm({ username: '', password: '', displayName: '', confirm: '' }); setError(''); }} sx={{ mb: 2.5 }}>
          <Tab label="Sign In" />
          <Tab label="Create Account" />
        </Tabs>

        {tab === 0 ? (
          <Box component="form" onSubmit={handleSignIn}>
            <TextField fullWidth label="Username" value={form.username} onChange={update('username')} autoFocus sx={{ mb: 2 }} />
            <TextField fullWidth type="password" label="Password" value={form.password} onChange={update('password')} error={!!error} helperText={error} sx={{ mb: 2 }} />
            <Button type="submit" variant="contained" fullWidth disabled={loading}>
              {loading ? <CircularProgress size={22} color="inherit" /> : 'Sign in'}
            </Button>
          </Box>
        ) : (
          <Box component="form" onSubmit={handleRegister}>
            <TextField fullWidth label="Display Name" placeholder="Sanket" value={form.displayName} onChange={update('displayName')} sx={{ mb: 2 }} />
            <TextField fullWidth label="Username *" placeholder="sanket" value={form.username} onChange={update('username')} autoFocus sx={{ mb: 2 }} />
            <TextField fullWidth type="password" label="Password *" value={form.password} onChange={update('password')} helperText="Minimum 6 characters" sx={{ mb: 2 }} />
            <TextField fullWidth type="password" label="Confirm Password *" value={form.confirm} onChange={update('confirm')} error={!!error} helperText={error || ' '} sx={{ mb: 2 }} />
            <Button type="submit" variant="contained" fullWidth disabled={loading}>
              {loading ? <CircularProgress size={22} color="inherit" /> : 'Create Account'}
            </Button>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5, textAlign: 'center' }}>
              Creates a new isolated household for your finances.
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}
