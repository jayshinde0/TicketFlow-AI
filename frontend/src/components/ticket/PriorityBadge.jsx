/**
 * PriorityBadge.jsx - Display priority level with color coding
 */

import React from 'react';

const PriorityBadge = ({ priority, size = 'md' }) => {
  const getColorClasses = () => {
    switch (priority?.toLowerCase()) {
      case 'critical':
        return 'bg-red-600 text-white border-red-700';
      case 'high':
        return 'bg-orange-500 text-white border-orange-600';
      case 'medium':
        return 'bg-yellow-500 text-white border-yellow-600';
      case 'low':
        return 'bg-green-500 text-white border-green-600';
      default:
        return 'bg-gray-500 text-white border-gray-600';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'text-xs px-2 py-0.5';
      case 'lg':
        return 'text-base px-4 py-2';
      default:
        return 'text-sm px-3 py-1';
    }
  };

  const getIcon = () => {
    switch (priority?.toLowerCase()) {
      case 'critical':
        return '🔴';
      case 'high':
        return '🟠';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full border ${getColorClasses()} ${getSizeClasses()}`}
    >
      <span>{getIcon()}</span>
      <span>{priority || 'Unknown'}</span>
    </span>
  );
};

export default PriorityBadge;
