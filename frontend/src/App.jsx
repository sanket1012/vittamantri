import { useEffect, useState } from 'react';
import api, { getMe } from './api/client.js';
import Dashboard from './pages/Dashboard.jsx';
import Landing from './pages/Landing.jsx';
import LoginGate from './components/LoginGate.jsx';

export default function App() {
  const [unlocked, setUnlocked] = useState(() => !!localStorage.getItem('jwt_token'));
  const [currentUser, setCurrentUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [authTab, setAuthTab] = useState(0);

  useEffect(() => {
    if (!unlocked) return;
    getMe()
      .then(setCurrentUser)
      .catch(() => {
        localStorage.removeItem('jwt_token');
        delete api.defaults.headers.common['Authorization'];
        setUnlocked(false);
        setCurrentUser(null);
      });
  }, [unlocked]);

  const handleUnlock = (user) => {
    setCurrentUser(user);
    setUnlocked(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    delete api.defaults.headers.common['Authorization'];
    setUnlocked(false);
    setCurrentUser(null);
  };

  if (!unlocked) {
    return <LoginGate onUnlock={handleUnlock} />;
  }

  return <Dashboard onLogout={handleLogout} currentUser={currentUser} />;
}
