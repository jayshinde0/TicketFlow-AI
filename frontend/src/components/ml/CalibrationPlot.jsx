/**
 * CalibrationPlot.jsx - Confidence calibration curve
 */

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const CalibrationPlot = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-64 text-gray-500">No calibration data available</div>;
  }

  const ece = data.ece || 0;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Confidence Calibration</h3>
      <p className="text-sm text-gray-600 mb-4">
        How well predicted confidence matches actual accuracy
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data.points || data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="predicted_confidence"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ value: 'Predicted Confidence', position: 'insideBottom', offset: -5 }}
            domain={[0, 1]}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ value: 'Actual Accuracy', angle: -90, position: 'insideLeft' }}
            domain={[0, 1]}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            formatter={(value) => value.toFixed(3)}
          />
          
          {/* Perfect calibration line */}
          <ReferenceLine
            segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
            stroke="#94a3b8"
            strokeDasharray="5 5"
            label={{ value: 'Perfect Calibration', position: 'top', fontSize: 10 }}
          />

          {/* Actual calibration */}
          <Line
            type="monotone"
            dataKey="actual_accuracy"
            stroke="#3b82f6"
            strokeWidth={3}
            name="Actual Calibration"
            dot={{ fill: '#3b82f6', r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-900">Expected Calibration Error (ECE)</p>
            <p className="text-xs text-blue-700">Lower is better (0 = perfect calibration)</p>
          </div>
          <p className="text-3xl font-bold text-blue-600">{ece.toFixed(4)}</p>
        </div>
      </div>
    </div>
  );
};

export default CalibrationPlot;
