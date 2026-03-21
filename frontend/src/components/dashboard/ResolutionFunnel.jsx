/**
 * ResolutionFunnel.jsx - Funnel chart showing resolution path
 */

import React from 'react';

const ResolutionFunnel = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available
      </div>
    );
  }

  const stages = [
    { key: 'total', label: 'All Tickets', color: 'bg-blue-500' },
    { key: 'auto_resolved', label: 'Auto-Resolved', color: 'bg-green-500' },
    { key: 'suggested', label: 'Suggested to Agent', color: 'bg-yellow-500' },
    { key: 'agent_approved', label: 'Agent Approved', color: 'bg-green-400' },
    { key: 'agent_edited', label: 'Agent Edited', color: 'bg-yellow-400' },
    { key: 'escalated', label: 'Escalated to Human', color: 'bg-red-500' }
  ];

  const maxValue = data.total || 1;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Resolution Path Funnel
      </h3>
      <p className="text-sm text-gray-600 mb-6">
        How tickets flow through the AI system
      </p>

      <div className="space-y-3">
        {stages.map((stage, index) => {
          const value = data[stage.key] || 0;
          const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
          const width = Math.max(percentage, 5); // Minimum 5% width for visibility

          return (
            <div key={stage.key} className="relative">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {stage.label}
                </span>
                <span className="text-sm text-gray-600">
                  {value} ({percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-8 overflow-hidden">
                <div
                  className={`${stage.color} h-full flex items-center justify-center text-white text-xs font-semibold transition-all duration-500`}
                  style={{ width: `${width}%` }}
                >
                  {percentage >= 10 && `${percentage.toFixed(0)}%`}
                </div>
              </div>
              {index < stages.length - 1 && (
                <div className="flex justify-center my-1">
                  <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-green-600">
            {data.auto_resolved && data.total
              ? ((data.auto_resolved / data.total) * 100).toFixed(1)
              : 0}%
          </p>
          <p className="text-xs text-gray-600">Auto-Resolution Rate</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-yellow-600">
            {data.suggested && data.total
              ? ((data.suggested / data.total) * 100).toFixed(1)
              : 0}%
          </p>
          <p className="text-xs text-gray-600">Agent Review Rate</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-red-600">
            {data.escalated && data.total
              ? ((data.escalated / data.total) * 100).toFixed(1)
              : 0}%
          </p>
          <p className="text-xs text-gray-600">Escalation Rate</p>
        </div>
      </div>
    </div>
  );
};

export default ResolutionFunnel;
