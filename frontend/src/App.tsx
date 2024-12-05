import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages';
import Machines from './pages/machines';
import './App.css';

function App() {
  return (
    <Router>
      <div style={{ display: 'flex', height: '100vh' }}>
        <div style={{ width: '250px', background: '#f4f4f4', padding: '10px' }}>
          <h2>PollySystem</h2>
          <nav>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li><NavLink to="/" style={{ textDecoration: 'none', color: '#333' }}>Status</NavLink></li>
              <li><NavLink to="/machines" style={{ textDecoration: 'none', color: '#333' }}>Hosts</NavLink></li>
            </ul>
          </nav>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/machines" element={<Machines />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
