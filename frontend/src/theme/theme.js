import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  },
  palette: {
    primary: { main: '#173F35', dark: '#0F2A23' },
    background: { default: '#F6F1E7', paper: '#FFFFFF' },
    text: { primary: '#202421', secondary: '#454940' },
    success: { main: '#059669', light: '#F0FDF4' },
    error: { main: '#DC2626', light: '#FEF2F2' },
    warning: { main: '#F59E0B', light: '#FFFBEB' },
  },
  shape: { borderRadius: 8 },
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
          borderColor: '#CFC7AE',
          color: '#454940',
          '&:hover': { borderColor: '#173F35', backgroundColor: '#F1ECDD' },
        },
      },
    },
    MuiCard: {
      defaultProps: { variant: 'outlined', elevation: 0 },
      styleOverrides: {
        root: {
          borderColor: '#E2DCC9',
          boxShadow: '0px 1px 2px 0px rgba(16,24,40,0.05)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: { backgroundColor: '#EDE7D8' },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          color: '#5B5F54',
          fontWeight: 500,
          fontSize: '0.857rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        },
        body: {
          fontSize: '0.875rem',
          color: '#202421',
          padding: '6px 16px',
          height: '60px',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { backgroundColor: '#FCF3DF' },
          borderBottom: '1px solid #E2DCC9',
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
          '& fieldset': { borderColor: '#CFC7AE' },
          '&:hover fieldset': { borderColor: '#173F35' },
          boxShadow: '0px 1px 2px 0px rgba(16,24,40,0.05)',
        },
      },
    },
  },
});

export default theme;
