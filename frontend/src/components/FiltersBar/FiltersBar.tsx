import React, { useState, useEffect } from 'react';
import { format, startOfWeek, startOfMonth, startOfQuarter, startOfYear, startOfDay, endOfDay } from 'date-fns';
import './FiltersBar.css';

export type PeriodType = 'today' | 'week' | 'month' | 'quarter' | 'year' | 'custom';

interface FiltersBarProps {
  onFilterChange: (params: { start_date: string; end_date: string }) => void;
  loading?: boolean;
}

const FiltersBar: React.FC<FiltersBarProps> = ({ onFilterChange, loading = false }) => {
  const [period, setPeriod] = useState<PeriodType>('today');
  const [startDate, setStartDate] = useState(format(startOfDay(new Date()), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(format(endOfDay(new Date()), 'yyyy-MM-dd'));
  const [showCustomRange, setShowCustomRange] = useState(false);

  // Применяем фильтры при инициализации
  useEffect(() => {
    const today = new Date();
    const start = startOfDay(today);
    const end = endOfDay(today);
    const startStr = format(start, 'yyyy-MM-dd');
    const endStr = format(end, 'yyyy-MM-dd');
    onFilterChange({
      start_date: startStr,
      end_date: endStr,
    });
  }, []); // Только при монтировании компонента

  const handlePeriodChange = (newPeriod: PeriodType) => {
    setPeriod(newPeriod);
    const today = new Date();
    let start: Date;
    let end: Date;

    switch (newPeriod) {
      case 'today':
        start = startOfDay(today);
        end = endOfDay(today);
        break;
      case 'week':
        // Неделя начинается с понедельника (weekStartsOn: 1)
        start = startOfWeek(today, { weekStartsOn: 1 });
        end = endOfDay(today);
        break;
      case 'month':
        start = startOfDay(startOfMonth(today));
        end = endOfDay(today);
        break;
      case 'quarter':
        start = startOfDay(startOfQuarter(today));
        end = endOfDay(today);
        break;
      case 'year':
        start = startOfDay(startOfYear(today));
        end = endOfDay(today);
        break;
      case 'custom':
        setShowCustomRange(true);
        return;
      default:
        start = startOfDay(today);
        end = endOfDay(today);
    }

    setShowCustomRange(false);
    const startStr = format(start, 'yyyy-MM-dd');
    const endStr = format(end, 'yyyy-MM-dd');
    setStartDate(startStr);
    setEndDate(endStr);

    applyFilters(startStr, endStr);
  };

  const applyFilters = (start: string, end: string) => {
    onFilterChange({
      start_date: start,
      end_date: end,
    });
  };

  const handleDateChange = () => {
    if (showCustomRange && startDate && endDate) {
      applyFilters(startDate, endDate);
    }
  };

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setStartDate(e.target.value);
    if (e.target.value && endDate) {
      applyFilters(e.target.value, endDate);
    }
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEndDate(e.target.value);
    if (startDate && e.target.value) {
      applyFilters(startDate, e.target.value);
    }
  };

  return (
    <div className="filters-bar">
      <div className="filters-row">
        <div className="filters-group">
          <label className="filters-label">Период:</label>
          <div className="period-buttons">
            {(['today', 'week', 'month', 'quarter', 'year'] as PeriodType[]).map((p) => (
              <button
                key={p}
                className={`period-btn ${period === p ? 'active' : ''}`}
                onClick={() => handlePeriodChange(p)}
                disabled={loading}
              >
                {p === 'today' ? 'Сегодня' :
                 p === 'week' ? 'Неделя' :
                 p === 'month' ? 'Месяц' :
                 p === 'quarter' ? 'Квартал' :
                 'Год'}
              </button>
            ))}
            <button
              className={`period-btn ${period === 'custom' ? 'active' : ''}`}
              onClick={() => handlePeriodChange('custom')}
              disabled={loading}
            >
              Диапазон
            </button>
          </div>
        </div>

        {showCustomRange && (
          <div className="filters-group">
            <label className="filters-label">Диапазон дат:</label>
            <input
              type="date"
              value={startDate}
              onChange={handleStartDateChange}
              className="date-input"
              disabled={loading}
            />
            <span className="date-separator">—</span>
            <input
              type="date"
              value={endDate}
              onChange={handleEndDateChange}
              className="date-input"
              disabled={loading}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default FiltersBar;

