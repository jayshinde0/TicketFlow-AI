/**
 * SLARiskAlert.jsx - SLA breach alert panel
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import PriorityBadge from '../ticket/PriorityBadge';
import SLATimer from '../ticket/SLATimer';

const SLARiskAlert = ({ tickets }) => {
  const navigate = useNavigate();

  if (!tickets || tickets.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          SLA Risk Alerts
        </h3>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">✅</div>
          <p>No SLA risks detected</p>
          <p className="text-sm">All tickets are within SLA limits</p>
        </div>
      </div>
    );
  }

  // Sort by SLA breach probability (highest first)
  const sortedTickets = [...tickets].sort(
    (a, b) =>
      (b.ai_analysis?.sla_breach_probability || 0) -
      (a.ai_analysis?.sla_breach_probability || 0)
  );

  const handleTicketClick = (ticketId) => {
    navigate(`/tickets/${ticketId}`);
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          SLA Risk Alerts
        </h3>
        <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-semibold">
          {tickets.length} at risk
        </span>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {sortedTickets.map((ticket) => {
          const ai = ticket.ai_analysis || {};
          const breachProb = (ai.sla_breach_probability * 100).toFixed(0);

          return (
            <div
              key={ticket.ticket_id}
              onClick={() => handleTicketClick(ticket.ticket_id)}
              className="p-4 border border-red-200 rounded-lg hover:bg-red-50 cursor-pointer transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm text-blue-600 font-semibold">
                      {ticket.ticket_id}
                    </span>
                    <PriorityBadge priority={ai.priority} size="sm" />
                  </div>
                  <p className="text-sm font-medium text-gray-900 line-clamp-1">
                    {ticket.subject}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-xs text-red-600 font-semibold mb-1">
                    {breachProb}% breach risk
                  </div>
                  <SLATimer
                    createdAt={ticket.created_at}
                    slaMinutes={ai.sla_minutes || 60}
                    size="sm"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-gray-600">
                <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                  {ai.category}
                </span>
                <span>•</span>
                <span>{new Date(ticket.created_at).toLocaleString()}</span>
              </div>

              {/* Progress bar */}
              <div className="mt-2 w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all"
                  style={{ width: `${breachProb}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {tickets.length > 5 && (
        <button
          onClick={() => navigate('/tickets?sla_risk=high')}
          className="mt-4 w-full py-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          View all {tickets.length} at-risk tickets →
        </button>
      )}
    </div>
  );
};

export default SLARiskAlert;
