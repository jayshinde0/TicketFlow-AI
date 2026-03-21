/**
 * useTickets.js - Custom hook for ticket data management
 * Handles fetching, filtering, and managing ticket state
 */

import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { toast } from 'react-hot-toast';

export const useTickets = (filters = {}) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
    total: 0,
    totalPages: 0
  });

  // Fetch tickets with filters
  const fetchTickets = useCallback(async (customFilters = {}) => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        ...filters,
        ...customFilters,
        page: pagination.page,
        limit: pagination.limit
      };

      const response = await api.get('/tickets', { params });
      
      setTickets(response.data.tickets || response.data);
      
      if (response.data.pagination) {
        setPagination(response.data.pagination);
      }
    } catch (err) {
      console.error('Failed to fetch tickets:', err);
      setError(err.response?.data?.detail || 'Failed to fetch tickets');
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.page, pagination.limit]);

  // Fetch single ticket by ID
  const fetchTicketById = useCallback(async (ticketId) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/tickets/${ticketId}`);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch ticket:', err);
      setError(err.response?.data?.detail || 'Failed to fetch ticket');
      toast.error('Failed to load ticket details');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Submit new ticket
  const submitTicket = useCallback(async (ticketData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/tickets', ticketData);
      toast.success(`Ticket ${response.data.ticket_id} created successfully!`);
      return response.data;
    } catch (err) {
      console.error('Failed to submit ticket:', err);
      setError(err.response?.data?.detail || 'Failed to submit ticket');
      toast.error('Failed to submit ticket');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update ticket status
  const updateTicketStatus = useCallback(async (ticketId, status, notes = '') => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.patch(`/tickets/${ticketId}/status`, {
        status,
        notes
      });
      
      // Update local state
      setTickets(prev => 
        prev.map(t => t.ticket_id === ticketId ? { ...t, status } : t)
      );
      
      toast.success(`Ticket status updated to ${status}`);
      return response.data;
    } catch (err) {
      console.error('Failed to update ticket:', err);
      setError(err.response?.data?.detail || 'Failed to update ticket');
      toast.error('Failed to update ticket status');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get LIME explanation for ticket
  const getExplanation = useCallback(async (ticketId) => {
    try {
      const response = await api.get(`/tickets/${ticketId}/explain`);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch explanation:', err);
      toast.error('Failed to load explanation');
      throw err;
    }
  }, []);

  // Get similar tickets
  const getSimilarTickets = useCallback(async (ticketId) => {
    try {
      const response = await api.get(`/tickets/${ticketId}/similar`);
      return response.data.similar_tickets || [];
    } catch (err) {
      console.error('Failed to fetch similar tickets:', err);
      toast.error('Failed to load similar tickets');
      throw err;
    }
  }, []);

  // Refresh tickets
  const refresh = useCallback(() => {
    fetchTickets();
  }, [fetchTickets]);

  // Change page
  const setPage = useCallback((newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  return {
    tickets,
    loading,
    error,
    pagination,
    fetchTickets,
    fetchTicketById,
    submitTicket,
    updateTicketStatus,
    getExplanation,
    getSimilarTickets,
    refresh,
    setPage
  };
};

// Hook for user's own tickets
export const useMyTickets = (userId) => {
  return useTickets({ user_id: userId });
};

// Hook for agent queue (tickets needing review)
export const useAgentQueue = (agentId) => {
  return useTickets({ 
    status: 'open',
    routing_decision: ['SUGGEST_TO_AGENT', 'ESCALATE_TO_HUMAN']
  });
};
