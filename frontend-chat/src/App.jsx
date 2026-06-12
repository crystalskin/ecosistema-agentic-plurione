import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import MetricsPage from './pages/MetricsPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <nav className="sidebar">
          <h2 className="logo">🤖 PluriOne</h2>
          <ul>
            <li><NavLink to="/" end className={({ isActive }) => isActive ? "active" : ""}>💬 Chat Agentic</NavLink></li>
            <li><NavLink to="/metrics" className={({ isActive }) => isActive ? "active" : ""}>📊 Métricas Módulo 7</NavLink></li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/metrics" element={<MetricsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;