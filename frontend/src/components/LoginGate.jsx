import { useState } from 'react';
import { Box, Button, TextField, Typography, Paper } from '@mui/material';

export default function LoginGate({ onUnlock }) {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!key.trim()) {
      setError('API key is required.');
      return;
    }
    localStorage.setItem('api_key', key.trim());
    onUnlock(key.trim());
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#f5f5f5">
      <Paper elevation={3} sx={{ p: 4, maxWidth: 380, width: '100%' }}>
        <Typography variant="h5" fontWeight={600} mb={1}>वित्तमंत्री</Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          Enter your dashboard API key to continue.
        </Typography>
        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            type="password"
            label="API Key"
            value={key}
            onChange={(e) => { setKey(e.target.value); setError(''); }}
            error={!!error}
            helperText={error}
            autoFocus
            sx={{ mb: 2 }}
          />
          <Button type="submit" variant="contained" fullWidth>Unlock</Button>
        </Box>
      </Paper>
    </Box>
  );
}
