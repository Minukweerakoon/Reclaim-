import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Voshan: Suspicious Behavior Detection Pages
import DetectionDashboard from './pages/voshan/DetectionDashboard';
import AlertHistory from './pages/voshan/AlertHistory';
import VideoUpload from './pages/voshan/VideoUpload';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="app-nav">
          <div className="nav-brand">
            <h1>🛡️ Reclaim - Lost and Found System</h1>
          </div>
          <div className="nav-links">
            <Link to="/voshan/detection">Detection Dashboard</Link>
            <Link to="/voshan/upload">Upload Video</Link>
            <Link to="/voshan/alerts">Alert History</Link>
          </div>
        </nav>

        <main className="app-main">
          <Routes>
            <Route path="/" element={
              <div className="home-page">
                <h2>Welcome to Reclaim</h2>
                <p>AI Powered Lost and Found System</p>
                <div className="quick-links">
                  <Link to="/voshan/detection" className="quick-link">
                    🛡️ Go to Detection Dashboard
                  </Link>
                  <Link to="/voshan/upload" className="quick-link">
                    📹 Upload Video for Detection
                  </Link>
                  <Link to="/voshan/alerts" className="quick-link">
                    📋 View Alert History
                  </Link>
                </div>
              </div>
            } />
            <Route path="/voshan/detection" element={<DetectionDashboard />} />
            <Route path="/voshan/upload" element={<VideoUpload />} />
            <Route path="/voshan/alerts" element={<AlertHistory />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

