/**
 * PredictionWidget.jsx - Volume forecast widget
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';

const PredictionWidget = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Volume Forecast
        </h3>
        <div className="flex items-center justify-center h-48 text-gray-500">
          No prediction data available
        </div>
      </div>
    );
  }

  // Calculate summary stats
  const totalPredicted = data.reduce((sum, d) => sum + (d.predicted || 0), 0);
  const avgPredicted = totalPredicted / data.length;
  const maxPredicted = Math.max(...data.map(d => d.predicted || 0));

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Volume Forecast (Next 24h)
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        AI-predicted ticket volume based on historical patterns
      </p>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">
            {totalPredicted.toFixed(0)}
          </p>
          <p className="text-xs text-gray-600">Total Expected</p>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <p className="text-2xl font-bold text-purple-600">
            {avgPredicted.toFixed(1)}
          </p>
          <p className="text-xs text-gray-600">Avg per Hour</p>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <p className="text-2xl font-bold text-orange-600">
            {maxPredicted.toFixed(0)}
          </p>
          <p className="text-xs text-gray-600">Peak Hour</p>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="hour"
            stroke="#6b7280"
            style={{ fontSize: '10px' }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '10px' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
          />
          <Area
            type="monotone"
            dataKey="predicted"
            stroke="#8b5cf6"
            strokeWidth={2}
            fill="url(#colorPredicted)"
            name="Predicted Tickets"
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Insights */}
      <div className="mt-4 p-3 bg-purple-50 rounded-lg">
        <p className="text-xs font-semibold text-purple-900 mb-1">
          📊 Forecast Insights
        </p>
        <ul className="text-xs text-purple-800 space-y-1">
          <li>• Peak expected at {data.find(d => d.predicted === maxPredicted)?.hour || 'N/A'}</li>
          <li>• {totalPredicted > 100 ? 'High' : totalPredicted > 50 ? 'Moderate' : 'Low'} volume expected</li>
          <li>• Confidence: {data[0]?.confidence ? `${(data[0].confidence * 100).toFixed(0)}%` : 'N/A'}</li>
        </ul>
      </div>
    </div>
  );
};

export default PredictionWidget;
