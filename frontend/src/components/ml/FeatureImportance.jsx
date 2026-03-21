/**
 * FeatureImportance.jsx - Top features bar chart
 */

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const CATEGORY_COLORS = {
  Network: '#3b82f6', Auth: '#10b981', Software: '#f59e0b', Hardware: '#ef4444',
  Access: '#8b5cf6', Billing: '#ec4899', Email: '#06b6d4', Security: '#dc2626',
  ServiceRequest: '#84cc16', Database: '#6366f1'
};

const FeatureImportance = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-64 text-gray-500">No feature data available</div>;
  }

  const topFeatures = data.slice(0, 15);

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Feature Importance</h3>
      <p className="text-sm text-gray-600 mb-4">Top 15 words driving classification</p>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={topFeatures} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis type="number" stroke="#6b7280" style={{ fontSize: '12px' }} />
          <YAxis type="category" dataKey="feature" stroke="#6b7280" style={{ fontSize: '11px' }} width={100} />
          <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {topFeatures.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.category] || '#94a3b8'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FeatureImportance;
