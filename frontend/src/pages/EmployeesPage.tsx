import React, { useState, useEffect } from 'react';
import { attendanceApi } from '../api/client';
import { AttendanceStatsResponse } from '../types';
import FiltersBar from '../components/FiltersBar/FiltersBar';
import KpiCards from '../components/KpiCards/KpiCards';
import EmployeesTable from '../components/EmployeesTable/EmployeesTable';
import { format, startOfDay } from 'date-fns';
import './EmployeesPage.css';

const EmployeesPage: React.FC = () => {
  const [stats, setStats] = useState<AttendanceStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (params?: {
    start_date?: string;
    end_date?: string;
  }) => {
    try {
      setLoading(true);
      setError(null);

      // Загружаем статистику
      const statsData = await attendanceApi.getStats(params);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load stats:', err);
      setError('Ошибка загрузки данных. Проверьте подключение к серверу.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Загружаем данные для сегодня по умолчанию
    const today = format(startOfDay(new Date()), 'yyyy-MM-dd');
    loadData({
      start_date: today,
      end_date: today,
    });
  }, []);

  const handleFilterChange = (params: {
    start_date: string;
    end_date: string;
  }) => {
    loadData(params);
  };

  if (error) {
    return (
      <div className="employees-page-error">
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
    <div className="employees-page">
      <div className="page-header">
        <h1 className="page-title">Мониторинг сотрудников</h1>
      </div>

      <FiltersBar
        onFilterChange={handleFilterChange}
        loading={loading}
      />

      {stats && (
        <>
          <KpiCards kpi={stats.kpi} />
          <EmployeesTable employees={stats.employees} loading={loading} />
        </>
      )}

      {loading && !stats && (
        <div className="page-loading">
          <div className="loading-spinner" />
          <p>Загрузка данных...</p>
        </div>
      )}
    </div>
  );
};

export default EmployeesPage;

