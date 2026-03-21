/**
 * GeneratedResponse.jsx - Display Mistral generated response
 */

import React from 'react';

const GeneratedResponse = ({ response, metadata }) => {
  if (!response) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Generated Response</h3>
        <div className="text-center py-8 text-gray-500">
          <p>No response generated</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">AI Generated Response</h3>
        {metadata?.model_used && (
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
            {metadata.model_used}
          </span>
        )}
      </div>

      {/* Response Text */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 mb-4">
        <p className="text-sm text-gray-900 whitespace-pre-wrap leading-relaxed">
          {response}
        </p>
      </div>

      {/* Metadata */}
      {metadata && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          {metadata.generation_time_ms && (
            <div className="p-2 bg-blue-50 rounded">
              <p className="text-gray-600">Generation Time</p>
              <p className="font-semibold text-blue-700">{metadata.generation_time_ms}ms</p>
            </div>
          )}
          {metadata.hallucination_detected !== undefined && (
            <div className={`p-2 rounded ${metadata.hallucination_detected ? 'bg-yellow-50' : 'bg-green-50'}`}>
              <p className="text-gray-600">Hallucination</p>
              <p className={`font-semibold ${metadata.hallucination_detected ? 'text-yellow-700' : 'text-green-700'}`}>
                {metadata.hallucination_detected ? 'Detected ⚠️' : 'None ✓'}
              </p>
            </div>
          )}
          {metadata.fallback_used !== undefined && (
            <div className="p-2 bg-purple-50 rounded">
              <p className="text-gray-600">Fallback Used</p>
              <p className="font-semibold text-purple-700">
                {metadata.fallback_used ? 'Yes' : 'No'}
              </p>
            </div>
          )}
          {metadata.model_used && (
            <div className="p-2 bg-gray-50 rounded">
              <p className="text-gray-600">Model</p>
              <p className="font-semibold text-gray-700">{metadata.model_used}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GeneratedResponse;
