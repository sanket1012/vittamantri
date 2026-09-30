import { createTheme } from '@mui/material/styles';

// Samvitta design tokens — Midnight + Ivory + Champagne, shared by the
// marketing site and the application. Deliberately not the standard
// "green = money" fintech palette.
export const tokens = {
  midnight: '#111827',
  navy: '#243044',
  ivory: '#F7F3EA',
  cardWhite: '#FCFBF8',
  champagne: '#C7A66A',
  bronze: '#A98252',
  ink: '#20242C',
  warmGray: '#77736D',
  stone: '#E3DDD4',
  coral: '#D96B67',
  indigo: '#6E72AE',
  mutedBlue: '#6583A5',
  selectedBg: '#F0EBE2',
};

// Editorial serif for headlines/brand moments; Inter stays the UI workhorse.
export const displayFontFamily = '"Instrument Serif", Georgia, serif';

const theme = createTheme({
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  },
  palette: {
    primary: { main: tokens.midnight, dark: '#0A0F1A' },
    // Champagne accent — used sparingly (3-5% of the UI) for premium moments,
    // not as a dominant color. Referenced as theme.palette.accent.main.
    accent: { main: tokens.champagne, dark: tokens.bronze, contrastText: tokens.midnight },
    background: { default: tokens.ivory, paper: tokens.cardWhite },
    text: { primary: tokens.ink, secondary: tokens.warmGray },
    success: { main: tokens.navy, light: '#EAEDF2' },
    error: { main: tokens.coral, light: '#FBEDED' },
    warning: { main: tokens.champagne, light: '#F6EFE1' },
    info: { main: tokens.mutedBlue, light: '#EAF0F5' },
    divider: tokens.stone,
  },
  shape: { borderRadius: 12 },
  shadows: [
    'none',
    '0px 1px 2px 0px rgba(17,24,39,0.05)',
    '0px 4px 12px rgba(17,24,39,0.08)',
    ...Array(23).fill('none'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'capitalize',
          fontWeight: 600,
          height: '44px',
          borderRadius: '10px',
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none' },
        },
        outlined: {
          borderColor: tokens.stone,
          color: tokens.ink,
          '&:hover': { borderColor: tokens.midnight, backgroundColor: tokens.selectedBg },
        },
      },
    },
    MuiCard: {
      defaultProps: { variant: 'outlined', elevation: 0 },
      styleOverrides: {
        root: {
          borderColor: tokens.stone,
          borderRadius: '18px',
          boxShadow: 'none',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: { backgroundColor: tokens.selectedBg },
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
          fontVariantNumeric: 'tabular-nums',
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
          borderRadius: '10px',
          '& fieldset': { borderColor: tokens.stone },
          '&:hover fieldset': { borderColor: tokens.midnight },
          boxShadow: 'none',
        },
      },
    },
  },
});

export default theme;
