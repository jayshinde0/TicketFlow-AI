/**
 * ConfidenceBadge.jsx - Display confidence score with color coding
 */

import React from 'react';

const ConfidenceBadge = ({ score, size = 'md', showLabel = true }) => {
  // Determine color based on confidence thresholds
  const getColorClasses = () => {
    if (score >= 0.85) {
      return 'bg-green-100 text-green-800 border-green-300';
    } else if (score >= 0.60) {
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    } else {
      return 'bg-red-100 text-red-800 border-red-300';
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
    if (score >= 0.85) return '✓';
    if (score >= 0.60) return '~';
    return '!';
  };

  const percentage = (score * 100).toFixed(1);

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full border ${getColorClasses()} ${getSizeClasses()}`}
      title={`Confidence: ${percentage}%`}
    >
      <span>{getIcon()}</span>
      <span>{percentage}%</span>
      {showLabel && size !== 'sm' && (
        <span className="font-normal opacity-75">confidence</span>
      )}
    </span>
  );
};

export default ConfidenceBadge;
