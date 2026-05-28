import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  },
  palette: {
    primary: { main: '#004EEB', dark: '#155EEF' },
    background: { default: '#F6F6F6', paper: '#FFFFFF' },
    text: { primary: '#101828', secondary: '#344054' },
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
          borderColor: '#D0D5DD',
          color: '#344054',
          '&:hover': { borderColor: '#004EEB', backgroundColor: '#F9FAFB' },
        },
      },
    },
    MuiCard: {
      defaultProps: { variant: 'outlined', elevation: 0 },
      styleOverrides: {
        root: {
          borderColor: '#EAECF0',
          boxShadow: '0px 1px 2px 0px rgba(16,24,40,0.05)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: { backgroundColor: '#F2F4F7' },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          color: '#475467',
          fontWeight: 500,
          fontSize: '0.857rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        },
        body: {
          fontSize: '0.875rem',
          color: '#101828',
          padding: '6px 16px',
          height: '60px',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { backgroundColor: '#FCF3DF' },
          borderBottom: '1px solid #EAECF0',
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
          '& fieldset': { borderColor: '#D0D5DD' },
          '&:hover fieldset': { borderColor: '#004EEB' },
          boxShadow: '0px 1px 2px 0px rgba(16,24,40,0.05)',
        },
      },
    },
  },
});

export default theme;
