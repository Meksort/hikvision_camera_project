import React, { useState, useEffect } from 'react';
import { topLateEmployeesApi } from '../api/client';
import { TopLateEmployee } from '../types';
import './HomePage.css';

const HomePage: React.FC = () => {
  const [employees, setEmployees] = useState<TopLateEmployee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTopLateEmployees();
  }, []);

  const loadTopLateEmployees = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await topLateEmployeesApi.getTopLate(10);
      setEmployees(data.employees);
    } catch (err) {
      console.error('Failed to load top late employees:', err);
      setError('Ошибка загрузки данных. Проверьте подключение к серверу.');
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="home-page-error">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="retry-btn">
            Обновить страницу
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="home-page">
      <div className="page-header">
        <h1 className="page-title">Главная</h1>
        <p className="page-subtitle">Сотрудники с наибольшим количеством опозданий</p>
      </div>

      {loading ? (
        <div className="home-page-loading">
          <div className="loading-spinner" />
          <p>Загрузка данных...</p>
        </div>
      ) : employees.length === 0 ? (
        <div className="home-page-empty">
          <p>Нет данных об опозданиях</p>
        </div>
      ) : (
        <div className="top-late-employees">
          <div className="employees-list">
            {employees.map((employee, index) => (
              <div key={employee.id} className="employee-card">
                <div className="employee-rank">
                  <span className="rank-number">#{index + 1}</span>
                </div>
                <div className="employee-avatar-container">
                  <img
                    src={employee.avatar}
                    alt={employee.name}
                    className="employee-avatar"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(employee.name)}&background=random&size=80`;
                    }}
                  />
                </div>
                <div className="employee-info">
                  <div className="employee-name">{employee.name}</div>
                  {employee.position && (
                    <div className="employee-position">{employee.position}</div>
                  )}
                  {employee.department && (
                    <div className="employee-department">{employee.department}</div>
                  )}
                </div>
                <div className="employee-stats">
                  <div className="stat-item late">
                    <div className="stat-icon">⏰</div>
                    <div className="stat-content">
                      <div className="stat-label">Опозданий</div>
                      <div className="stat-value">{employee.lateCount}</div>
                    </div>
                  </div>
                  <div className="stat-item early">
                    <div className="stat-icon">🚪</div>
                    <div className="stat-content">
                      <div className="stat-label">Ранних уходов</div>
                      <div className="stat-value">{employee.earlyLeaveCount}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;


