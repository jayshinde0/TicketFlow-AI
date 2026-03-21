/**
 * AgentWorkload.jsx - Bar chart showing agent workload
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

const AgentWorkload = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No agents data available
      </div>
    );
  }

  // Color based on load percentage
  const getBarColor = (current, max) => {
    const percentage = (current / max) * 100;
    if (percentage >= 90) return '#ef4444'; // Red - overloaded
    if (percentage >= 70) return '#f59e0b'; // Yellow - high load
    return '#10b981'; // Green - normal
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Agent Workload
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Current ticket load per agent
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            width={100}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
            formatter={(value, name, props) => {
              const { current_load, max_load } = props.payload;
              const percentage = ((current_load / max_load) * 100).toFixed(0);
              return [`${value} / ${max_load} (${percentage}%)`, 'Current Load'];
            }}
          />
          <Bar dataKey="current_load" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry.current_load, entry.max_load)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Agent Stats Table */}
      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Agent
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Load
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Resolved
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Avg Time
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Approval Rate
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.map((agent, index) => {
              const loadPercentage = ((agent.current_load / agent.max_load) * 100).toFixed(0);
              const loadColor =
                loadPercentage >= 90
                  ? 'text-red-600 font-bold'
                  : loadPercentage >= 70
                  ? 'text-yellow-600'
                  : 'text-green-600';

              return (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium text-gray-900">
                    {agent.name}
                  </td>
                  <td className={`px-3 py-2 ${loadColor}`}>
                    {agent.current_load} / {agent.max_load} ({loadPercentage}%)
                  </td>
                  <td className="px-3 py-2 text-gray-600">
                    {agent.tickets_resolved || 0}
                  </td>
                  <td className="px-3 py-2 text-gray-600">
                    {agent.avg_resolution_time?.toFixed(1) || 0}h
                  </td>
                  <td className="px-3 py-2 text-gray-600">
                    {agent.approval_rate?.toFixed(1) || 0}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AgentWorkload;
