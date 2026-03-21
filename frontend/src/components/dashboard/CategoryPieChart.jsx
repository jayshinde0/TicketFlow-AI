/**
 * CategoryPieChart.jsx - Pie chart showing category distribution
 */

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const COLORS = {
  Network: '#3b82f6',
  Auth: '#10b981',
  Software: '#f59e0b',
  Hardware: '#ef4444',
  Access: '#8b5cf6',
  Billing: '#ec4899',
  Email: '#06b6d4',
  Security: '#dc2626',
  ServiceRequest: '#84cc16',
  Database: '#6366f1'
};

const CategoryPieChart = ({ data, onCategoryClick }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available
      </div>
    );
  }

  const handleClick = (entry) => {
    if (onCategoryClick) {
      onCategoryClick(entry.category);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Category Distribution
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="category"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ category, percent }) =>
              `${category} (${(percent * 100).toFixed(0)}%)`
            }
            onClick={handleClick}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.category] || '#94a3b8'}
                className="cursor-pointer hover:opacity-80 transition-opacity"
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CategoryPieChart;
