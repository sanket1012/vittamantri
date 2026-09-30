import { createTheme } from '@mui/material/styles';

// Samvitta design tokens — Midnight + Champagne + Ivory.
// Deliberately not the standard "green = money" fintech palette.
export const tokens = {
  midnight: '#15171C',
  navy: '#20242D',
  ivory: '#F5F1E8',
  cardWhite: '#FBFAF7',
  champagne: '#C8A76A',
  amber: '#D99A3C',
  ink: '#18191C',
  warmGray: '#77736C',
  stone: '#DDD7CD',
  coral: '#D96767',
  indigo: '#6F78C9',
  mutedBlue: '#5E83A9',
};

// Editorial serif for headlines/brand moments; Inter stays the UI workhorse.
export const displayFontFamily = '"Instrument Serif", Georgia, serif';

const theme = createTheme({
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  },
  palette: {
    primary: { main: tokens.midnight, dark: '#0B0C0F' },
    // Champagne accent — used sparingly (3-5% of the UI) for premium moments,
    // not as a dominant color. Referenced as theme.palette.accent.main.
    accent: { main: tokens.champagne, contrastText: tokens.ink },
    background: { default: tokens.ivory, paper: tokens.cardWhite },
    text: { primary: tokens.ink, secondary: tokens.warmGray },
    success: { main: '#4F9D6E', light: '#E9F2EB' },
    error: { main: tokens.coral, light: '#FBEDED' },
    warning: { main: tokens.amber, light: '#FBF1E2' },
    info: { main: tokens.mutedBlue, light: '#EAF0F5' },
    divider: tokens.stone,
  },
  shape: { borderRadius: 12 },
  shadows: [
    'none',
    '0px 1px 2px 0px rgba(21,23,28,0.05)',
    '0px 4px 12px rgba(21,23,28,0.08)',
    ...Array(23).fill('none'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'capitalize',
          fontWeight: 600,
          height: '44px',
          borderRadius: '8px',
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none' },
        },
        outlined: {
          borderColor: tokens.stone,
          color: tokens.ink,
          '&:hover': { borderColor: tokens.midnight, backgroundColor: '#F0EEE7' },
        },
      },
    },
    MuiCard: {
      defaultProps: { variant: 'outlined', elevation: 0 },
      styleOverrides: {
        root: {
          borderColor: tokens.stone,
          borderRadius: '1.25rem',
          boxShadow: '0px 1px 2px 0px rgba(21,23,28,0.04)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: { backgroundColor: '#F0EEE7' },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          color: tokens.warmGray,
          fontWeight: 500,
          fontSize: '0.857rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        },
        body: {
          fontSize: '0.875rem',
          color: tokens.ink,
          padding: '6px 16px',
          height: '60px',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { backgroundColor: tokens.ivory },
          borderBottom: `1px solid ${tokens.stone}`,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, fontSize: '0.75rem', borderRadius: '6px' },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          minHeight: '44px',
          borderRadius: '8px',
          '& fieldset': { borderColor: tokens.stone },
          '&:hover fieldset': { borderColor: tokens.midnight },
          boxShadow: '0px 1px 2px 0px rgba(21,23,28,0.04)',
        },
      },
    },
  },
});

export default theme;
