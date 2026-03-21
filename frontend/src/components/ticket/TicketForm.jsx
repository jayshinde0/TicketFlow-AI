/**
 * TicketForm.jsx - Ticket submission form
 */

import React, { useState } from 'react';
import { toast } from 'react-hot-toast';

const CATEGORIES = [
  'Network',
  'Auth',
  'Software',
  'Hardware',
  'Access',
  'Billing',
  'Email',
  'Security',
  'ServiceRequest',
  'Database'
];

const TicketForm = ({ onSubmit, loading = false }) => {
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    category: '', // Optional - AI will predict
    attachment: null
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('File size must be less than 5MB');
        return;
      }
      setFormData(prev => ({ ...prev, attachment: file }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.subject.trim()) {
      newErrors.subject = 'Subject is required';
    } else if (formData.subject.length < 5) {
      newErrors.subject = 'Subject must be at least 5 characters';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.length < 20) {
      newErrors.description = 'Description must be at least 20 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      toast.error('Please fix the errors in the form');
      return;
    }

    try {
      await onSubmit(formData);
      // Reset form on success
      setFormData({
        subject: '',
        description: '',
        category: '',
        attachment: null
      });
    } catch (error) {
      // Error handling done in parent
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Subject */}
      <div>
        <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
          Subject <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="subject"
          name="subject"
          value={formData.subject}
          onChange={handleChange}
          placeholder="Brief description of your issue"
          className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            errors.subject ? 'border-red-500' : 'border-gray-300'
          }`}
          disabled={loading}
        />
        {errors.subject && (
          <p className="mt-1 text-sm text-red-600">{errors.subject}</p>
        )}
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          Description <span className="text-red-500">*</span>
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Provide detailed information about your issue (minimum 20 characters)"
          rows={6}
          className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            errors.description ? 'border-red-500' : 'border-gray-300'
          }`}
          disabled={loading}
        />
        <div className="flex justify-between items-center mt-1">
          {errors.description ? (
            <p className="text-sm text-red-600">{errors.description}</p>
          ) : (
            <p className="text-sm text-gray-500">
              {formData.description.length} characters
            </p>
          )}
        </div>
      </div>

      {/* Category (Optional) */}
      <div>
        <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
          Category <span className="text-gray-400 text-xs">(Optional - AI will predict)</span>
        </label>
        <select
          id="category"
          name="category"
          value={formData.category}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={loading}
        >
          <option value="">Let AI predict the category</option>
          {CATEGORIES.map(cat => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* File Attachment */}
      <div>
        <label htmlFor="attachment" className="block text-sm font-medium text-gray-700 mb-2">
          Attachment <span className="text-gray-400 text-xs">(Optional - Screenshots, logs, etc.)</span>
        </label>
        <input
          type="file"
          id="attachment"
          name="attachment"
          onChange={handleFileChange}
          accept="image/*,.pdf,.txt,.log"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={loading}
        />
        {formData.attachment && (
          <p className="mt-1 text-sm text-gray-600">
            📎 {formData.attachment.name} ({(formData.attachment.size / 1024).toFixed(1)} KB)
          </p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          Max file size: 5MB. Supported formats: images, PDF, text files
        </p>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className={`px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 transition-colors ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Submitting...
            </span>
          ) : (
            'Submit Ticket'
          )}
        </button>
      </div>
    </form>
  );
};

export default TicketForm;
