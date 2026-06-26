import { useState } from 'react';
import { Box, Button, TextField, Typography, Paper, CircularProgress } from '@mui/material';
import api from '../api/client.js';

export default function LoginGate({ onUnlock }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Username and password are required.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/login', { username: username.trim(), password });
      localStorage.setItem('jwt_token', data.token);
      api.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
      onUnlock(data.user);
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#f5f5f5">
      <Paper elevation={3} sx={{ p: 4, maxWidth: 380, width: '100%' }}>
        <Typography variant="h5" fontWeight={600} mb={0.5}>वित्तमंत्री</Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>Family Finance — Sign in to continue</Typography>
        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => { setUsername(e.target.value); setError(''); }}
            autoFocus
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            type="password"
            label="Password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setError(''); }}
            error={!!error}
            helperText={error}
            sx={{ mb: 2 }}
          />
          <Button type="submit" variant="contained" fullWidth disabled={loading}>
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Sign in'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
