import { useEffect, useRef, useState } from 'react';
import TelegramIcon from '@mui/icons-material/Telegram';
import { Box, Button, CircularProgress, Typography } from '@mui/material';
import toast from 'react-hot-toast';
import { createTelegramLinkToken, getMe } from '../api/client.js';

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 2 * 60 * 1000;

/** "Connect Telegram" button: opens a one-tap /start deep link, then polls
 * /api/me until the bot confirms the link, so the user never has to look up
 * or paste their numeric Telegram ID. */
export default function ConnectTelegram({ onLinked }) {
  const [status, setStatus] = useState('idle'); // idle | opening | waiting | linked | error
  const pollRef = useRef(null);

  useEffect(() => () => clearInterval(pollRef.current), []);

  const handleConnect = async () => {
    setStatus('opening');
    try {
      const { deep_link: deepLink } = await createTelegramLinkToken();
      if (!deepLink) throw new Error('no_deep_link');
      window.open(deepLink, '_blank', 'noopener');
      setStatus('waiting');

      const startedAt = Date.now();
      pollRef.current = setInterval(async () => {
        if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
          clearInterval(pollRef.current);
          setStatus('idle');
          return;
        }
        try {
          const me = await getMe();
          if (me.telegram_id) {
            clearInterval(pollRef.current);
            setStatus('linked');
            toast.success('Telegram connected!');
            onLinked?.(me);
          }
        } catch {
          // ignore transient poll failures
        }
      }, POLL_INTERVAL_MS);
    } catch {
      setStatus('error');
      toast.error('Could not start Telegram connection. Try again.');
    }
  };

  if (status === 'linked') {
    return <Typography sx={{ color: '#173F35', fontWeight: 600, fontSize: '0.875rem' }}>✅ Telegram connected!</Typography>;
  }

  return (
    <Box>
      <Button
        variant="contained"
        startIcon={status === 'waiting' ? <CircularProgress size={16} color="inherit" /> : <TelegramIcon />}
        onClick={handleConnect}
        disabled={status === 'opening' || status === 'waiting'}
        sx={{ bgcolor: '#229ED9', '&:hover': { bgcolor: '#1b87ba' } }}
      >
        {status === 'waiting' ? 'Waiting for Telegram…' : 'Connect Telegram'}
      </Button>
      {status === 'waiting' && (
        <Typography sx={{ color: '#6B6F63', fontSize: '0.8rem', mt: 1 }}>
          A Telegram tab just opened — tap "Start" there. This page will update automatically once it's connected.
        </Typography>
      )}
    </Box>
  );
}
