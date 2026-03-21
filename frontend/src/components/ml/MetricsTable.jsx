/**
 * MetricsTable.jsx - F1/precision/recall table per category
 */

import React from 'react';

const MetricsTable = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No metrics data available
      </div>
    );
  }

  const getF1Color = (f1) => {
    if (f1 >= 0.85) return 'text-green-600 bg-green-50';
    if (f1 >= 0.75) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getTrendIcon = (trend) => {
    if (trend > 0) return <span className="text-green-600">↑ {trend.toFixed(2)}</span>;
    if (trend < 0) return <span className="text-red-600">↓ {Math.abs(trend).toFixed(2)}</span>;
    return <span className="text-gray-600">→ 0.00</span>;
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Per-Domain Metrics
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Classification performance for each ticket category
      </p>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Domain
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Precision
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Recall
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                F1 Score
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Support
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Trend
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="font-semibold text-gray-900">{row.domain}</span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm text-gray-900">
                    {row.precision.toFixed(3)}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm text-gray-900">
                    {row.recall.toFixed(3)}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getF1Color(row.f1)}`}>
                    {row.f1.toFixed(3)}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                  {row.support}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {row.trend !== undefined ? getTrendIcon(row.trend) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-gray-100">
            <tr>
              <td className="px-4 py-3 font-bold text-gray-900">
                Macro Average
              </td>
              <td className="px-4 py-3 font-semibold text-gray-900">
                {(data.reduce((sum, r) => sum + r.precision, 0) / data.length).toFixed(3)}
              </td>
              <td className="px-4 py-3 font-semibold text-gray-900">
                {(data.reduce((sum, r) => sum + r.recall, 0) / data.length).toFixed(3)}
              </td>
              <td className="px-4 py-3 font-semibold text-gray-900">
                {(data.reduce((sum, r) => sum + r.f1, 0) / data.length).toFixed(3)}
              </td>
              <td className="px-4 py-3 font-semibold text-gray-900">
                {data.reduce((sum, r) => sum + r.support, 0)}
              </td>
              <td className="px-4 py-3"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Performance Targets */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm font-semibold text-blue-900 mb-2">🎯 Performance Targets</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <span className="text-blue-700">Overall F1:</span>
            <span className="ml-1 font-semibold">≥ 0.85</span>
          </div>
          <div>
            <span className="text-blue-700">Auth F1:</span>
            <span className="ml-1 font-semibold">≥ 0.90</span>
          </div>
          <div>
            <span className="text-blue-700">Security Recall:</span>
            <span className="ml-1 font-semibold">≥ 0.98</span>
          </div>
          <div>
            <span className="text-blue-700">Billing F1:</span>
            <span className="ml-1 font-semibold">≥ 0.88</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsTable;
