/**
 * LIMEExplanation.jsx - LIME word importance visualization
 */

import React from 'react';

const LIMEExplanation = ({ explanation }) => {
  if (!explanation || !explanation.top_positive_features) {
    return <div className="text-gray-500 text-sm">No explanation available</div>;
  }

  const { top_positive_features, top_negative_features, predicted_class, explanation_confidence } = explanation;

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-900">AI Explanation (LIME)</h4>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
          {predicted_class} ({(explanation_confidence * 100).toFixed(1)}%)
        </span>
      </div>

      {/* Positive Features */}
      <div className="mb-4">
        <p className="text-xs font-medium text-green-700 mb-2">✓ Words supporting prediction:</p>
        <div className="space-y-1">
          {top_positive_features.map((feature, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
                <div
                  className="bg-green-500 h-full flex items-center px-2"
                  style={{ width: `${Math.abs(feature.weight) * 100}%` }}
                >
                  <span className="text-xs font-semibold text-white">{feature.word}</span>
                </div>
              </div>
              <span className="text-xs text-gray-600 w-12 text-right">
                +{feature.weight.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Negative Features */}
      {top_negative_features && top_negative_features.length > 0 && (
        <div>
          <p className="text-xs font-medium text-red-700 mb-2">✗ Words against prediction:</p>
          <div className="space-y-1">
            {top_negative_features.map((feature, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
                  <div
                    className="bg-red-500 h-full flex items-center justify-end px-2"
                    style={{ width: `${Math.abs(feature.weight) * 100}%` }}
                  >
                    <span className="text-xs font-semibold text-white">{feature.word}</span>
                  </div>
                </div>
                <span className="text-xs text-gray-600 w-12 text-right">
                  {feature.weight.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LIMEExplanation;
