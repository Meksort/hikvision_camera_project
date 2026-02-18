import React, { useState } from 'react';
import './ProgressBar.css';

interface ProgressBarProps {
  productivePercent: number;
  distractionPercent: number;
  idlePercent: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  productivePercent,
  distractionPercent,
  idlePercent,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const totalPercent = Math.min(
    productivePercent + distractionPercent + idlePercent,
    100
  );

  return (
    <div
      className="progress-bar-container"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="progress-bar">
        <div
          className="progress-segment productive"
          style={{ width: `${productivePercent}%` }}
          title={`Продуктивно: ${productivePercent.toFixed(1)}%`}
        />
        <div
          className="progress-segment distraction"
          style={{ width: `${distractionPercent}%` }}
          title={`Отвлечения: ${distractionPercent.toFixed(1)}%`}
        />
        <div
          className="progress-segment idle"
          style={{ width: `${idlePercent}%` }}
          title={`Простой: ${idlePercent.toFixed(1)}%`}
        />
      </div>
      {showTooltip && (
        <div className="progress-tooltip">
          <div className="tooltip-item">
            <span className="tooltip-color productive" />
            <span>Продуктивно: {productivePercent.toFixed(1)}%</span>
          </div>
          <div className="tooltip-item">
            <span className="tooltip-color distraction" />
            <span>Отвлечения: {distractionPercent.toFixed(1)}%</span>
          </div>
          <div className="tooltip-item">
            <span className="tooltip-color idle" />
            <span>Простой: {idlePercent.toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressBar;


