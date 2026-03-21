/**
 * ConfidenceHistogram.jsx - Histogram showing confidence score distribution
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const ConfidenceHistogram = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available
      </div>
    );
  }

  // Get bar color based on confidence range
  const getBarColor = (range) => {
    const value = parseFloat(range.split('-')[0]);
    if (value >= 0.85) return '#10b981'; // Green
    if (value >= 0.60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Confidence Score Distribution
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Shows how confident the AI is in its predictions
      </p>
      
      {/* Legend */}
      <div className="flex items-center gap-4 mb-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span>&lt; 0.60 (Escalate)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-yellow-500 rounded"></div>
          <span>0.60-0.85 (Suggest)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded"></div>
          <span>&gt; 0.85 (Auto-Resolve)</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="range"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ value: 'Confidence Score', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ value: 'Number of Tickets', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <ReferenceLine
            x="0.60-0.70"
            stroke="#f59e0b"
            strokeDasharray="3 3"
            label={{ value: 'Suggest Threshold', position: 'top', fontSize: 10 }}
          />
          <ReferenceLine
            x="0.80-0.90"
            stroke="#10b981"
            strokeDasharray="3 3"
            label={{ value: 'Auto-Resolve Threshold', position: 'top', fontSize: 10 }}
          />
          <Bar
            dataKey="count"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.range)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ConfidenceHistogram;
