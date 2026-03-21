/**
 * TicketQueue.jsx - Live ticket queue table with filters
 */

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import PriorityBadge from './PriorityBadge';
import ConfidenceBadge from './ConfidenceBadge';
import SLATimer from './SLATimer';

const TicketQueue = ({ tickets, loading = false, onTicketClick }) => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    category: '',
    priority: '',
    routing: '',
    search: ''
  });
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Filter and sort tickets
  const filteredTickets = useMemo(() => {
    let filtered = [...tickets];

    // Apply filters
    if (filters.category) {
      filtered = filtered.filter(t => t.ai_analysis?.category === filters.category);
    }
    if (filters.priority) {
      filtered = filtered.filter(t => t.ai_analysis?.priority === filters.priority);
    }
    if (filters.routing) {
      filtered = filtered.filter(t => t.ai_analysis?.routing_decision === filters.routing);
    }
    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter(t =>
        t.ticket_id.toLowerCase().includes(search) ||
        t.subject.toLowerCase().includes(search) ||
        t.description.toLowerCase().includes(search)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case 'priority':
          const priorityOrder = { Critical: 4, High: 3, Medium: 2, Low: 1 };
          aVal = priorityOrder[a.ai_analysis?.priority] || 0;
          bVal = priorityOrder[b.ai_analysis?.priority] || 0;
          break;
        case 'confidence':
          aVal = a.ai_analysis?.confidence_score || 0;
          bVal = b.ai_analysis?.confidence_score || 0;
          break;
        case 'created_at':
          aVal = new Date(a.created_at).getTime();
          bVal = new Date(b.created_at).getTime();
          break;
        default:
          return 0;
      }

      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return filtered;
  }, [tickets, filters, sortBy, sortOrder]);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleRowClick = (ticket) => {
    if (onTicketClick) {
      onTicketClick(ticket);
    } else {
      navigate(`/tickets/${ticket.ticket_id}`);
    }
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case 'POSITIVE': return '😊';
      case 'NEGATIVE': return '😠';
      case 'NEUTRAL': return '😐';
      default: return '';
    }
  };

  const getRoutingBadge = (decision) => {
    switch (decision) {
      case 'AUTO_RESOLVE':
        return <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">🤖 Auto</span>;
      case 'SUGGEST_TO_AGENT':
        return <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">👤 Review</span>;
      case 'ESCALATE_TO_HUMAN':
        return <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">⚠️ Escalate</span>;
      default:
        return <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">-</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <input
            type="text"
            placeholder="Search tickets..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />

          {/* Category Filter */}
          <select
            value={filters.category}
            onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            <option value="Network">Network</option>
            <option value="Auth">Auth</option>
            <option value="Software">Software</option>
            <option value="Hardware">Hardware</option>
            <option value="Access">Access</option>
            <option value="Billing">Billing</option>
            <option value="Email">Email</option>
            <option value="Security">Security</option>
            <option value="ServiceRequest">Service Request</option>
            <option value="Database">Database</option>
          </select>

          {/* Priority Filter */}
          <select
            value={filters.priority}
            onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          {/* Routing Filter */}
          <select
            value={filters.routing}
            onChange={(e) => setFilters(prev => ({ ...prev, routing: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Routing</option>
            <option value="AUTO_RESOLVE">Auto Resolve</option>
            <option value="SUGGEST_TO_AGENT">Suggest to Agent</option>
            <option value="ESCALATE_TO_HUMAN">Escalate</option>
          </select>
        </div>

        <div className="mt-2 text-sm text-gray-600">
          Showing {filteredTickets.length} of {tickets.length} tickets
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subject
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('priority')}
                >
                  Priority {sortBy === 'priority' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('confidence')}
                >
                  Confidence {sortBy === 'confidence' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sentiment
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SLA
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Routing
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('created_at')}
                >
                  Created {sortBy === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTickets.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                    No tickets found
                  </td>
                </tr>
              ) : (
                filteredTickets.map((ticket) => {
                  const ai = ticket.ai_analysis || {};
                  return (
                    <tr
                      key={ticket.ticket_id}
                      onClick={() => handleRowClick(ticket)}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="font-mono text-sm text-blue-600 font-semibold">
                          {ticket.ticket_id}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900 line-clamp-1">
                          {ticket.subject}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                          {ai.category || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {ai.priority ? <PriorityBadge priority={ai.priority} size="sm" /> : '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {ai.confidence_score ? (
                          <ConfidenceBadge score={ai.confidence_score} size="sm" showLabel={false} />
                        ) : '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        {getSentimentIcon(ai.sentiment_label)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {ticket.status === 'open' && ai.sla_breach_probability > 0.5 ? (
                          <SLATimer
                            createdAt={ticket.created_at}
                            slaMinutes={ai.sla_minutes || 60}
                            size="sm"
                          />
                        ) : (
                          <span className="text-xs text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {getRoutingBadge(ai.routing_decision)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-500">
                        {new Date(ticket.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TicketQueue;
