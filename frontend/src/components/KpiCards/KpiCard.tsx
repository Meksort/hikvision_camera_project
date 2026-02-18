import React from 'react';
import './KpiCard.css';

interface KpiCardProps {
  title: string;
  percent: number;
  time: string;
  trend?: number;
  color: 'green' | 'yellow' | 'red' | 'blue';
  icon: string;
}

const KpiCard: React.FC<KpiCardProps> = ({ title, percent, time, trend, color, icon }) => {
  const getColorClass = () => {
    switch (color) {
      case 'green':
        return 'kpi-card-green';
      case 'yellow':
        return 'kpi-card-yellow';
      case 'red':
        return 'kpi-card-red';
      case 'blue':
        return 'kpi-card-blue';
      default:
        return '';
    }
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    if (trend > 0) return '↗️';
    if (trend < 0) return '↘️';
    return '➡️';
  };

  return (
    <div className={`kpi-card ${getColorClass()}`}>
      <div className="kpi-card-header">
        <div className="kpi-icon">{icon}</div>
        <div className="kpi-title">{title}</div>
      </div>
      <div className="kpi-card-body">
        <div className="kpi-percent">{percent.toFixed(1)}%</div>
        <div className="kpi-time">{time}</div>
        {trend !== undefined && (
          <div className={`kpi-trend ${trend > 0 ? 'positive' : trend < 0 ? 'negative' : 'neutral'}`}>
            {getTrendIcon()} {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
      <div className="kpi-indicator">
        <div
          className="kpi-indicator-fill"
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  );
};

export default KpiCard;


