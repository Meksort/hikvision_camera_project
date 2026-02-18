import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar/Sidebar';
import HomePage from './pages/HomePage';
import EmployeesPage from './pages/EmployeesPage';
import ReportsPage from './pages/ReportsPage';
import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/employees" element={<EmployeesPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/cameras" element={<div>Камеры (в разработке)</div>} />
            <Route path="/settings" element={<div>Настройки (в разработке)</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;

