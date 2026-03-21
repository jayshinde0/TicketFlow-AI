/**
 * TicketCard.jsx - Ticket display card with all key information
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import PriorityBadge from './PriorityBadge';
import ConfidenceBadge from './ConfidenceBadge';
import SLATimer from './SLATimer';

const TicketCard = ({ ticket, onClick }) => {
  const navigate = useNavigate();
  const ai = ticket.ai_analysis || {};
  
  const handleClick = () => {
    if (onClick) {
      onClick(ticket);
    } else {
      navigate(`/tickets/${ticket.ticket_id}`);
    }
  };

  const getStatusColor = () => {
    switch (ticket.status) {
      case 'open':
        return 'bg-blue-100 text-blue-800';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'closed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoutingBadge = () => {
    const decision = ai.routing_decision;
    switch (decision) {
      case 'AUTO_RESOLVE':
        return <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">🤖 Auto</span>;
      case 'SUGGEST_TO_AGENT':
        return <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">👤 Review</span>;
      case 'ESCALATE_TO_HUMAN':
        return <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">⚠️ Escalate</span>;
      default:
        return null;
    }
  };

  const getSentimentIcon = () => {
    switch (ai.sentiment_label) {
      case 'POSITIVE':
        return '😊';
      case 'NEGATIVE':
        return '😠';
      case 'NEUTRAL':
        return '😐';
      default:
        return '';
    }
  };

  return (
    <div
      onClick={handleClick}
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-sm text-blue-600 font-semibold">
              {ticket.ticket_id}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor()}`}>
              {ticket.status}
            </span>
            {getRoutingBadge()}
          </div>
          <h3 className="font-semibold text-gray-900 line-clamp-1">
            {ticket.subject}
          </h3>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 line-clamp-2 mb-3">
        {ticket.description}
      </p>

      {/* AI Analysis */}
      {ai.category && (
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded font-medium">
            {ai.category}
          </span>
          <PriorityBadge priority={ai.priority} size="sm" />
          {ai.confidence_score && (
            <ConfidenceBadge score={ai.confidence_score} size="sm" showLabel={false} />
          )}
          {ai.sentiment_label && (
            <span className="text-xs" title={ai.sentiment_label}>
              {getSentimentIcon()}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t">
        <span>
          {new Date(ticket.created_at).toLocaleString()}
        </span>
        {ai.sla_breach_probability > 0.7 && ticket.status === 'open' && (
          <SLATimer
            createdAt={ticket.created_at}
            slaMinutes={ai.sla_minutes || 60}
            size="sm"
          />
        )}
      </div>
    </div>
  );
};

export default TicketCard;
