import { useEffect, useRef } from 'react';
import { Box, Typography } from '@mui/material';
import toast from 'react-hot-toast';
import api from '../api/client.js';

const BOT_USERNAME = 'MyChancellorBot';

/** Telegram's official "Log in with Telegram" widget: verified server-side via
 * HMAC, no redirect away from our own domain, and (with data-request-access)
 * grants the bot permission to message the user immediately — no /start needed. */
export default function ConnectTelegram({ onLinked }) {
  const containerRef = useRef(null);

  useEffect(() => {
    window.onTelegramAuth = async (telegramUser) => {
      try {
        const { data } = await api.post('/me/telegram/verify', telegramUser);
        toast.success('Telegram connected! Check Telegram for a welcome message.');
        onLinked?.(data);
      } catch (err) {
        toast.error(err.response?.data?.error || 'Could not verify Telegram login.');
      }
    };

    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.async = true;
    script.setAttribute('data-telegram-login', BOT_USERNAME);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '8');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    containerRef.current?.appendChild(script);

    return () => {
      delete window.onTelegramAuth;
    };
  }, []);

  return (
    <Box>
      <Box ref={containerRef} sx={{ display: 'flex', justifyContent: 'center', minHeight: 40 }} />
      <Typography sx={{ color: '#6B6F63', fontSize: '0.75rem', mt: 1, textAlign: 'center' }}>
        Verified directly by Telegram — you'll get a welcome message as soon as you approve.
      </Typography>
    </Box>
  );
}
