import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  },
  palette: {
    primary: { main: '#123F36', dark: '#0B2B24' },
    // Emerald accent — used for positive figures, active states, and
    // highlights. Not a MUI-standard palette key, referenced explicitly as
    // theme.palette.accent.main.
    accent: { main: '#16A477', contrastText: '#FFFFFF' },
    background: { default: '#F7F8F5', paper: '#FFFFFF' },
    text: { primary: '#17211E', secondary: '#737B77' },
    success: { main: '#16A477', light: '#E5F5EF' },
    error: { main: '#E5534B', light: '#FDF0EF' },
    warning: { main: '#F59E0B', light: '#FFFBEB' },
    divider: '#E7E9E5',
  },
  shape: { borderRadius: 12 },
  shadows: [
    'none',
    '0px 1px 2px 0px rgba(16,24,40,0.05)',
    '0px 4px 12px rgba(0,0,0,0.08)',
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
          borderColor: '#E7E9E5',
          color: '#17211E',
          '&:hover': { borderColor: '#123F36', backgroundColor: '#F0F3F1' },
        },
      },
    },
    MuiCard: {
      defaultProps: { variant: 'outlined', elevation: 0 },
      styleOverrides: {
        root: {
          borderColor: '#E7E9E5',
          borderRadius: '1rem',
          boxShadow: '0px 1px 2px 0px rgba(16,24,40,0.04)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: { backgroundColor: '#F0F3F1' },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          color: '#737B77',
          fontWeight: 500,
          fontSize: '0.857rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        },
        body: {
          fontSize: '0.875rem',
          color: '#17211E',
          padding: '6px 16px',
          height: '60px',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { backgroundColor: '#F7F8F5' },
          borderBottom: '1px solid #E7E9E5',
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
          '& fieldset': { borderColor: '#E7E9E5' },
          '&:hover fieldset': { borderColor: '#123F36' },
          boxShadow: '0px 1px 2px 0px rgba(16,24,40,0.04)',
        },
      },
    },
  },
});

export default theme;
