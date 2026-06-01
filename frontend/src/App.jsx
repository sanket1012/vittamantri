import { useState } from 'react';
import Dashboard from './pages/Dashboard.jsx';
import LoginGate from './components/LoginGate.jsx';
import api from './api/client.js';

function getStoredKey() {
  return localStorage.getItem('api_key') || '';
}

export default function App() {
  const [unlocked, setUnlocked] = useState(() => !!getStoredKey());

  const handleUnlock = () => {
    setUnlocked(true);
  };

  if (!unlocked) {
    return <LoginGate onUnlock={handleUnlock} />;
  }

  return <Dashboard />;
}
