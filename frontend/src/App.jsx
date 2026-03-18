import React, { useState, useEffect, useRef } from 'react';
import { Keyboard, MousePointer2, Power, Camera, LayoutDashboard } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

const App = () => {
  const [activeMode, setActiveMode] = useState('MENU');
  const [status, setStatus] = useState('System Ready');
  const [activeModifiers, setActiveModifiers] = useState([]);
  const [volume, setVolume] = useState(50);
  const [isConnected, setIsConnected] = useState(false);
  const videoRef = useRef(null);

  // WebSocket Connection
  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws');
    
    socket.onopen = () => {
      setIsConnected(true);
      window.AI_SOCKET = socket;
      console.log('Connected to AI Backend');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'status') {
        setStatus(data.message);
        if (data.mode) setActiveMode(data.mode);
      }
      if (data.type === 'modifiers') setActiveModifiers(data.data || data.modifiers);
      if (data.type === 'volume') setVolume(Math.round(data.data * 100));
    };

    socket.onclose = () => setIsConnected(false);
    
    return () => socket.close();
  }, []);

  const modes = [
    { id: 'KEYBOARD', icon: <Keyboard size={32} />, label: 'Air Typing', desc: 'Type globally with hand gestures.' },
    { id: 'MOUSE', icon: <MousePointer2 size={32} />, label: 'Hand Mouse', desc: 'Control OS cursor with precision.' }
  ];

  const handleModeChange = (modeId) => {
    setActiveMode(modeId);
    if (isConnected) {
      window.AI_SOCKET.send(JSON.stringify({
        type: 'mode_change',
        data: modeId
      }));
    }
  };

  return (
    <div className="app-container">
      <header className="header glass-card">
        <h1>Gesture Control Suite</h1>
        <div className="status-badge" style={{ color: isConnected ? '#00ff00' : '#ff0000' }}>
          {isConnected ? 'BACKEND ONLINE' : 'DISCONNECTED'}
        </div>
      </header>

      <main className="main-content">
        <AnimatePresence mode="wait">
          {activeMode === 'MENU' ? (
            <motion.div 
              key="menu"
              className="menu-simple"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {modes.map((mode) => (
                <div key={mode.id} className="mode-card-wrapper">
                  <button 
                    className="simple-mode-btn glass-card"
                    onClick={() => handleModeChange(mode.id)}
                  >
                    {mode.icon}
                    <span>{mode.label}</span>
                    <div className="open-btn-overlay">
                      OPEN {mode.id === 'KEYBOARD' ? 'KEYBOARD' : 'MOUSE'}
                    </div>
                  </button>
                </div>
              ))}
              <button className="simple-mode-btn exit glass-card" onClick={() => window.close()}>
                <Power />
                <span>Exit</span>
              </button>
            </motion.div>
          ) : (
            <motion.div 
              key="active"
              className="active-simple"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <div className="mode-status glass-card">
                <h2>{activeMode} ACTIVE</h2>
                <p className="pulse">{status}</p>
                <div className="modifier-display">
                   {activeModifiers.map(m => <span key={m} className="mod-tag">{m}</span>)}
                </div>
                <button className="back-simple-btn" onClick={() => handleModeChange('MENU')}>
                  BACK TO MENU
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="footer-simple">
        <p>CV Processing active in background...</p>
      </footer>
    </div>
  );
};

export default App;
