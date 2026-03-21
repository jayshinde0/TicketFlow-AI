/**
 * SimilarTickets.jsx - Display similar past tickets
 */

import React, { useState } from 'react';
import PriorityBadge from '../ticket/PriorityBadge';

const SimilarTickets = ({ tickets }) => {
  const [expandedId, setExpandedId] = useState(null);

  if (!tickets || tickets.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Similar Past Tickets</h3>
        <div className="text-center py-8 text-gray-500">
          <p>No similar tickets found</p>
        </div>
      </div>
    );
  }

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Similar Past Tickets
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Top {tickets.length} most similar resolved tickets from knowledge base
      </p>

      <div className="space-y-3">
        {tickets.map((ticket, idx) => {
          const isExpanded = expandedId === ticket.id;
          const similarity = (ticket.similarity_score * 100).toFixed(1);

          return (
            <div
              key={ticket.id || idx}
              className="border border-gray-200 rounded-lg overflow-hidden hover:border-blue-300 transition-colors"
            >
              {/* Header */}
              <div
                onClick={() => toggleExpand(ticket.id)}
                className="p-4 cursor-pointer hover:bg-gray-50"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-blue-600 font-semibold">
                        {ticket.id}
                      </span>
                      {ticket.category && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                          {ticket.category}
                        </span>
                      )}
                      {ticket.priority && <PriorityBadge priority={ticket.priority} size="sm" />}
                    </div>
                    <p className="text-sm font-medium text-gray-900 line-clamp-2">
                      {ticket.text || ticket.subject}
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-lg font-bold text-green-600">{similarity}%</div>
                    <div className="text-xs text-gray-500">similarity</div>
                  </div>
                </div>

                {/* Preview */}
                {!isExpanded && ticket.solution && (
                  <p className="text-xs text-gray-600 line-clamp-2 mt-2">
                    {ticket.solution}
                  </p>
                )}

                {/* Expand indicator */}
                <div className="flex items-center justify-center mt-2">
                  <span className="text-xs text-blue-600">
                    {isExpanded ? '▲ Click to collapse' : '▼ Click to expand solution'}
                  </span>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-200 bg-gray-50">
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-700 mb-2">Full Solution:</p>
                    <div className="p-3 bg-white rounded border border-gray-200">
                      <p className="text-sm text-gray-900 whitespace-pre-wrap">
                        {ticket.solution}
                      </p>
                    </div>
                  </div>

                  {ticket.resolution_time && (
                    <div className="mt-2 text-xs text-gray-600">
                      ⏱ Resolved in: {ticket.resolution_time}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SimilarTickets;
