import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

interface MenuItem {
  path: string;
  label: string;
  icon: string;
}

const menuItems: MenuItem[] = [
  { path: '/', label: 'Главная', icon: '🏠' },
  { path: '/employees', label: 'Сотрудники', icon: '👥' },
  { path: '/reports', label: 'Отчёты', icon: '📊' },
  { path: '/cameras', label: 'Камеры', icon: '📷' },
  { path: '/settings', label: 'Настройки', icon: '⚙️' },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">Hikvision Monitor</h1>
      </div>
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          // Проверяем точное совпадение пути
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-icon">{item.icon}</span>
              <span className="sidebar-label">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
};

export default Sidebar;

