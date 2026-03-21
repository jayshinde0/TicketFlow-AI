/**
 * ReviewPanel.jsx - Agent review panel with approve/edit/reject actions
 */

import React, { useState } from 'react';
import { toast } from 'react-hot-toast';

const ReviewPanel = ({ ticket, generatedResponse, onAction, loading = false }) => {
  const [editedResponse, setEditedResponse] = useState(generatedResponse || '');
  const [feedbackNote, setFeedbackNote] = useState('');
  const [action, setAction] = useState(null);

  const handleApprove = async () => {
    setAction('approve');
    try {
      await onAction('approve', { response: generatedResponse, note: feedbackNote });
      toast.success('Response approved and sent!');
    } catch (error) {
      toast.error('Failed to approve');
    } finally {
      setAction(null);
    }
  };

  const handleEdit = async () => {
    if (!editedResponse.trim()) {
      toast.error('Response cannot be empty');
      return;
    }
    setAction('edit');
    try {
      await onAction('edit', { response: editedResponse, note: feedbackNote });
      toast.success('Edited response sent!');
    } catch (error) {
      toast.error('Failed to save edit');
    } finally {
      setAction(null);
    }
  };

  const handleReject = async () => {
    setAction('reject');
    try {
      await onAction('reject', { note: feedbackNote || 'AI response rejected' });
      toast.success('Ticket marked for manual resolution');
    } catch (error) {
      toast.error('Failed to reject');
    } finally {
      setAction(null);
    }
  };

  const handleEscalate = async () => {
    setAction('escalate');
    try {
      await onAction('escalate', { note: feedbackNote || 'Escalated to senior engineer' });
      toast.success('Ticket escalated!');
    } catch (error) {
      toast.error('Failed to escalate');
    } finally {
      setAction(null);
    }
  };

  const isLoading = loading || action !== null;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Review & Action</h3>

      {/* Generated Response */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          AI Generated Response
        </label>
        <textarea
          value={editedResponse}
          onChange={(e) => setEditedResponse(e.target.value)}
          rows={8}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Edit the AI response if needed..."
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          {editedResponse.length} characters
        </p>
      </div>

      {/* Hallucination Warning */}
      {ticket?.ai_analysis?.hallucination_detected && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-yellow-600 text-lg">⚠️</span>
            <div>
              <p className="text-sm font-semibold text-yellow-900">Hallucination Detected</p>
              <p className="text-xs text-yellow-700">
                The AI response may not be accurate. Please review carefully before approving.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Note */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Feedback Note (Optional)
        </label>
        <textarea
          value={feedbackNote}
          onChange={(e) => setFeedbackNote(e.target.value)}
          rows={2}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Add notes for the learning agent..."
          disabled={isLoading}
        />
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={handleApprove}
          disabled={isLoading}
          className="px-4 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 focus:ring-4 focus:ring-green-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {action === 'approve' ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Approving...
            </span>
          ) : (
            '✓ Approve'
          )}
        </button>

        <button
          onClick={handleEdit}
          disabled={isLoading}
          className="px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {action === 'edit' ? 'Saving...' : '✎ Edit & Approve'}
        </button>

        <button
          onClick={handleReject}
          disabled={isLoading}
          className="px-4 py-3 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 focus:ring-4 focus:ring-red-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {action === 'reject' ? 'Rejecting...' : '✗ Reject'}
        </button>

        <button
          onClick={handleEscalate}
          disabled={isLoading}
          className="px-4 py-3 bg-orange-600 text-white font-semibold rounded-lg hover:bg-orange-700 focus:ring-4 focus:ring-orange-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {action === 'escalate' ? 'Escalating...' : '⚠ Escalate to Senior'}
        </button>
      </div>
    </div>
  );
};

export default ReviewPanel;
