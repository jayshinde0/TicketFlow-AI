/**
 * RootCauseAlert.jsx - Root cause detection alert feed
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';

const RootCauseAlert = ({ alerts }) => {
  const navigate = useNavigate();

  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Root Cause Alerts
        </h3>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🔍</div>
          <p>No incidents detected</p>
          <p className="text-sm">System is monitoring for ticket spikes</p>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'P0':
        return 'bg-red-600 text-white';
      case 'P1':
        return 'bg-orange-500 text-white';
      case 'P2':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'open':
        return 'bg-red-100 text-red-700';
      case 'investigating':
        return 'bg-yellow-100 text-yellow-700';
      case 'resolved':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleAlertClick = (alertId) => {
    navigate(`/admin/root-cause/${alertId}`);
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Root Cause Alerts
        </h3>
        <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-semibold">
          {alerts.filter(a => a.status === 'open').length} active
        </span>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.map((alert) => (
          <div
            key={alert.alert_id}
            onClick={() => handleAlertClick(alert.alert_id)}
            className="p-4 border border-orange-200 rounded-lg hover:bg-orange-50 cursor-pointer transition-colors"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs font-bold ${getSeverityColor(alert.severity)}`}>
                  {alert.severity}
                </span>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(alert.status)}`}>
                  {alert.status}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {new Date(alert.timestamp).toLocaleString()}
              </span>
            </div>

            {/* Category and Count */}
            <div className="mb-2">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-semibold text-gray-900">
                  {alert.category}
                </span>
                <span className="text-xs text-gray-600">
                  • {alert.ticket_count} tickets in {alert.time_window_minutes} min
                </span>
              </div>
            </div>

            {/* Root Cause Hypothesis */}
            <div className="mb-2">
              <p className="text-sm text-gray-700 italic">
                💡 {alert.root_cause_hypothesis}
              </p>
            </div>

            {/* Keywords */}
            {alert.common_keywords && alert.common_keywords.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {alert.common_keywords.slice(0, 5).map((keyword, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            )}

            {/* Affected Tickets */}
            {alert.affected_ticket_ids && alert.affected_ticket_ids.length > 0 && (
              <div className="mt-2 text-xs text-gray-600">
                Affected tickets: {alert.affected_ticket_ids.slice(0, 3).join(', ')}
                {alert.affected_ticket_ids.length > 3 && ` +${alert.affected_ticket_ids.length - 3} more`}
              </div>
            )}
          </div>
        ))}
      </div>

      {alerts.length > 5 && (
        <button
          onClick={() => navigate('/admin/root-cause-alerts')}
          className="mt-4 w-full py-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          View all {alerts.length} alerts →
        </button>
      )}
    </div>
  );
};

export default RootCauseAlert;
