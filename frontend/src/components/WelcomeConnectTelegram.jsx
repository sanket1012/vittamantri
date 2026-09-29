import { Box, Button, Paper, Typography } from '@mui/material';
import BrandMark from './BrandMark.jsx';
import ConnectTelegram from './ConnectTelegram.jsx';

/** Shown once, right after registration, so a new user connects Telegram with
 * a single tap instead of discovering the manual ID-linking flow later. */
export default function WelcomeConnectTelegram({ displayName, onDone }) {
  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#F6F1E7" px={2}>
      <Paper elevation={3} sx={{ p: 4, maxWidth: 440, width: '100%', textAlign: 'center' }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <BrandMark size={40} />
        </Box>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Welcome{displayName ? `, ${displayName}` : ''}!
        </Typography>
        <Typography sx={{ color: '#6B6F63', fontSize: '0.9rem', mb: 3 }}>
          One last step — connect Telegram so you can log expenses just by messaging the bot.
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <ConnectTelegram onLinked={onDone} />
        </Box>
        <Button onClick={onDone} sx={{ color: '#6B6F63', fontSize: '0.8125rem' }}>
          Skip for now
        </Button>
      </Paper>
    </Box>
  );
}
