import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import BarChartIcon from '@mui/icons-material/BarChart';
import GroupsIcon from '@mui/icons-material/Groups';
import LockIcon from '@mui/icons-material/Lock';
import SendIcon from '@mui/icons-material/Send';
import { Box, Button, Card, CardContent, Grid, Typography } from '@mui/material';

const FEATURES = [
  {
    icon: GroupsIcon,
    title: 'Built for the whole family',
    description: 'Every household gets its own isolated space. Invite members, track who logged what, and see a shared picture of your finances.',
  },
  {
    icon: SendIcon,
    title: 'Log expenses from Telegram',
    description: 'Message the bot in plain English — "450 on groceries at Dmart" — and it’s parsed, categorized, and saved instantly.',
  },
  {
    icon: AutoAwesomeIcon,
    title: 'Smart auto-categorization',
    description: 'Transactions are matched to the right category automatically, with full control to customize categories and subcategories.',
  },
  {
    icon: BarChartIcon,
    title: 'Real analytics, not spreadsheets',
    description: 'Monthly trends, category breakdowns, and per-member summaries — plus one-click CSV export whenever you need the raw data.',
  },
  {
    icon: LockIcon,
    title: 'Private by design',
    description: 'Your household’s data is fully isolated from every other household. Nobody else can see your numbers.',
  },
];

export default function Landing({ onGetStarted }) {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#FFFFFF', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ px: { xs: 2.5, md: 6 }, py: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #EAECF0' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ width: 40, height: 40, borderRadius: '10px', bgcolor: '#EFF6FF', color: '#004EEB', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <AccountBalanceWalletIcon />
          </Box>
          <Typography sx={{ fontSize: 18, fontWeight: 700, color: '#101828' }}>वित्तमंत्री</Typography>
        </Box>
        <Button variant="outlined" onClick={() => onGetStarted(0)}>
          Sign In
        </Button>
      </Box>

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', px: { xs: 2.5, md: 6 }, py: { xs: 6, md: 10 } }}>
        <Box sx={{ maxWidth: 720, textAlign: 'center', mb: { xs: 6, md: 8 } }}>
          <Typography sx={{ fontSize: { xs: 32, md: 44 }, fontWeight: 700, color: '#101828', lineHeight: 1.15, mb: 2 }}>
            Family finances,{' '}
            <Box component="span" sx={{ color: '#004EEB' }}>
              tracked together
            </Box>
          </Typography>
          <Typography sx={{ fontSize: { xs: 16, md: 18 }, color: '#667085', lineHeight: 1.6, mb: 4 }}>
            वित्तमंत्री (VittaMantri) is a household finance tracker with a Telegram bot that logs
            expenses as you text them, smart categorization, and clean analytics — built for
            families who want to manage money without spreadsheets.
          </Typography>
          <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large" onClick={() => onGetStarted(1)} sx={{ px: 4 }}>
              Get Started — It's Free
            </Button>
            <Button variant="outlined" size="large" onClick={() => onGetStarted(0)} sx={{ px: 4 }}>
              Sign In
            </Button>
          </Box>
        </Box>

        <Grid container spacing={2.5} sx={{ maxWidth: 1100 }}>
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <Grid item xs={12} sm={6} md={4} key={feature.title}>
                <Card variant="outlined" sx={{ borderRadius: '0.75rem', height: '100%' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ width: 44, height: 44, borderRadius: '10px', bgcolor: '#EFF6FF', color: '#004EEB', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                      <Icon />
                    </Box>
                    <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#101828', mb: 1 }}>{feature.title}</Typography>
                    <Typography sx={{ fontSize: '0.875rem', color: '#667085', lineHeight: 1.6 }}>{feature.description}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </Box>

      <Box sx={{ px: { xs: 2.5, md: 6 }, py: 3, borderTop: '1px solid #EAECF0', textAlign: 'center' }}>
        <Typography sx={{ fontSize: '0.8125rem', color: '#98A2B3' }}>वित्तमंत्री — a personal project for tracking family finances.</Typography>
      </Box>
    </Box>
  );
}
