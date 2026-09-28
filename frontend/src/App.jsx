import { useEffect, useState } from 'react';
import api, { getMe } from './api/client.js';
import Dashboard from './pages/Dashboard.jsx';
import Landing from './pages/Landing.jsx';
import LoginGate from './components/LoginGate.jsx';
import WelcomeConnectTelegram from './components/WelcomeConnectTelegram.jsx';

export default function App() {
  const [unlocked, setUnlocked] = useState(() => !!localStorage.getItem('jwt_token'));
  const [currentUser, setCurrentUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [authTab, setAuthTab] = useState(0);
  const [justRegistered, setJustRegistered] = useState(false);

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

  const handleRegistered = (user) => {
    setCurrentUser(user);
    setUnlocked(true);
    setJustRegistered(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    delete api.defaults.headers.common['Authorization'];
    setUnlocked(false);
    setCurrentUser(null);
  };

  if (!unlocked) {
    if (!showAuth) {
      return (
        <Landing
          onGetStarted={(tab) => {
            setAuthTab(tab);
            setShowAuth(true);
          }}
        />
      );
    }
    return <LoginGate onUnlock={handleUnlock} initialTab={authTab} onBack={() => setShowAuth(false)} />;
  }

  return <Dashboard onLogout={handleLogout} currentUser={currentUser} />;
}
