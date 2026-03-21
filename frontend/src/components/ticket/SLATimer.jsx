/**
 * SLATimer.jsx - Live countdown timer for SLA deadline
 */

import React, { useState, useEffect } from 'react';

const SLATimer = ({ createdAt, slaMinutes, size = 'md' }) => {
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [percentage, setPercentage] = useState(100);

  useEffect(() => {
    const calculateTimeRemaining = () => {
      const created = new Date(createdAt);
      const deadline = new Date(created.getTime() + slaMinutes * 60000);
      const now = new Date();
      const remaining = deadline - now;

      if (remaining <= 0) {
        setTimeRemaining({ breached: true });
        setPercentage(0);
        return;
      }

      const totalMs = slaMinutes * 60000;
      const pct = (remaining / totalMs) * 100;
      setPercentage(pct);

      const hours = Math.floor(remaining / 3600000);
      const minutes = Math.floor((remaining % 3600000) / 60000);
      const seconds = Math.floor((remaining % 60000) / 1000);

      setTimeRemaining({ hours, minutes, seconds, breached: false });
    };

    calculateTimeRemaining();
    const interval = setInterval(calculateTimeRemaining, 1000);

    return () => clearInterval(interval);
  }, [createdAt, slaMinutes]);

  if (!timeRemaining) {
    return <span className="text-gray-400">Loading...</span>;
  }

  if (timeRemaining.breached) {
    return (
      <span className="inline-flex items-center gap-1 text-red-600 font-bold">
        <span className="animate-pulse">🔴</span>
        <span>SLA BREACHED</span>
      </span>
    );
  }

  const getColorClass = () => {
    if (percentage > 50) return 'text-green-600';
    if (percentage > 20) return 'text-yellow-600';
    return 'text-red-600 font-bold animate-pulse';
  };

  const formatTime = () => {
    const { hours, minutes, seconds } = timeRemaining;
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return 'text-xs';
      case 'lg':
        return 'text-lg';
      default:
        return 'text-sm';
    }
  };

  return (
    <div className="inline-flex items-center gap-2">
      <span className={`${getColorClass()} ${getSizeClass()} font-mono`}>
        ⏰ {formatTime()}
      </span>
      {size !== 'sm' && (
        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-1000 ${
              percentage > 50
                ? 'bg-green-500'
                : percentage > 20
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default SLATimer;
