import React from 'react';
import ReactDOM from 'react-dom/client';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from '@mui/material/styles';
import { Toaster } from 'react-hot-toast';
import App from './App.jsx';
import './styles.css';
import theme from './theme/theme.js';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
      <Toaster position="top-right" toastOptions={{ style: { background: '#FFFFFF', color: '#101828', border: '1px solid #EAECF0' } }} />
    </ThemeProvider>
  </React.StrictMode>,
);
