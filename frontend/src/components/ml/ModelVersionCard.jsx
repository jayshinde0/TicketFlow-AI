/**
 * ModelVersionCard.jsx - Model version information card
 */

import React from 'react';

const ModelVersionCard = ({ version }) => {
  if (!version) {
    return <div className="text-gray-500 text-sm">No version data available</div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Model Version {version.version}</h3>
          <p className="text-sm text-gray-600">Trained on {new Date(version.trained_at).toLocaleDateString()}</p>
        </div>
        {version.is_active && (
          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
            Active
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">{version.category_f1?.toFixed(3) || 'N/A'}</p>
          <p className="text-xs text-gray-600">Category F1</p>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <p className="text-2xl font-bold text-purple-600">{version.priority_f1?.toFixed(3) || 'N/A'}</p>
          <p className="text-xs text-gray-600">Priority F1</p>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <p className="text-2xl font-bold text-green-600">{version.sla_auc?.toFixed(3) || 'N/A'}</p>
          <p className="text-xs text-gray-600">SLA AUC</p>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <p className="text-2xl font-bold text-orange-600">{version.training_size?.toLocaleString() || 'N/A'}</p>
          <p className="text-xs text-gray-600">Training Size</p>
        </div>
      </div>

      {version.feedback_examples_added > 0 && (
        <div className="p-3 bg-yellow-50 rounded-lg">
          <p className="text-sm text-yellow-800">
            📚 +{version.feedback_examples_added} feedback examples added since last version
          </p>
        </div>
      )}
    </div>
  );
};

export default ModelVersionCard;
