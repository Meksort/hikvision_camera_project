import React from 'react';
import KpiCard from './KpiCard';
import './KpiCards.css';

interface KpiCardsProps {
  kpi: {
    workedPercent: number;
    workedTime: string;
    productivePercent: number;
    productiveTime: string;
    idlePercent: number;
    idleTime: string;
    distractionPercent: number;
    distractionTime: string;
    trend: {
      worked: number;
      productive: number;
      idle: number;
      distraction: number;
    };
  };
}

const KpiCards: React.FC<KpiCardsProps> = ({ kpi }) => {
  return (
    <div className="kpi-cards">
      <KpiCard
        title="Отработано"
        percent={kpi.workedPercent}
        time={kpi.workedTime}
        trend={kpi.trend.worked}
        color="blue"
        icon="⏱️"
      />
      <KpiCard
        title="Продуктивно"
        percent={kpi.productivePercent}
        time={kpi.productiveTime}
        trend={kpi.trend.productive}
        color="green"
        icon="✅"
      />
      <KpiCard
        title="Простой"
        percent={kpi.idlePercent}
        time={kpi.idleTime}
        trend={kpi.trend.idle}
        color="yellow"
        icon="⏸️"
      />
      <KpiCard
        title="Отвлечения"
        percent={kpi.distractionPercent}
        time={kpi.distractionTime}
        trend={kpi.trend.distraction}
        color="red"
        icon="⚠️"
      />
    </div>
  );
};

export default KpiCards;


