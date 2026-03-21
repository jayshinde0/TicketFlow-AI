/**
 * SentimentChart.jsx - Line chart showing sentiment trends
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const SentimentChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Sentiment Trend
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Customer sentiment over time (last 24 hours)
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="hour"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ value: 'Hour', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
            formatter={(value) => `${value.toFixed(1)}%`}
          />
          <Legend />
          
          {/* Alert threshold line */}
          <ReferenceLine
            y={40}
            stroke="#ef4444"
            strokeDasharray="3 3"
            label={{
              value: 'Alert Threshold (40%)',
              position: 'right',
              fill: '#ef4444',
              fontSize: 10
            }}
          />

          <Line
            type="monotone"
            dataKey="positive"
            stroke="#10b981"
            strokeWidth={2}
            name="Positive 😊"
            dot={{ fill: '#10b981', r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="neutral"
            stroke="#6b7280"
            strokeWidth={2}
            name="Neutral 😐"
            dot={{ fill: '#6b7280', r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="negative"
            stroke="#ef4444"
            strokeWidth={2}
            name="Negative 😠"
            dot={{ fill: '#ef4444', r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Current Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-lg font-bold text-green-600">
            {data[data.length - 1]?.positive?.toFixed(1) || 0}%
          </p>
          <p className="text-xs text-gray-600">Positive Now</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-lg font-bold text-gray-600">
            {data[data.length - 1]?.neutral?.toFixed(1) || 0}%
          </p>
          <p className="text-xs text-gray-600">Neutral Now</p>
        </div>
        <div className="p-3 bg-red-50 rounded-lg">
          <p className="text-lg font-bold text-red-600">
            {data[data.length - 1]?.negative?.toFixed(1) || 0}%
          </p>
          <p className="text-xs text-gray-600">Negative Now</p>
        </div>
      </div>
    </div>
  );
};

export default SentimentChart;
