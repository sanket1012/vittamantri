// TEMPORARY local-only visual check — not part of the app, never imported by
// index.html/main.jsx, and not committed. Renders the real Dashboard with a
// mock user so its layout/colors can be screenshotted without hitting the
// production API (the /api proxy target isn't running locally, so fetches
// just fail harmlessly and the components show their empty states).
import ReactDOM from 'react-dom/client';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme/theme.js';
import Dashboard from './pages/Dashboard.jsx';
import './styles.css';

const mockUser = { display_name: 'Sanket Waghmare', username: 'sanket', role: 'admin', household_id: 1 };

ReactDOM.createRoot(document.getElementById('root')).render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <Dashboard currentUser={mockUser} onLogout={() => {}} />
  </ThemeProvider>,
);
