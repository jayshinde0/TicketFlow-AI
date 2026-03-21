/**
 * ConfusionMatrix.jsx - Visual confusion matrix for model evaluation
 */

import React from 'react';

const ConfusionMatrix = ({ data }) => {
  if (!data || !data.matrix || !data.labels) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No confusion matrix data available
      </div>
    );
  }

  const { matrix, labels } = data;
  const maxValue = Math.max(...matrix.flat());

  // Get color intensity based on value
  const getColor = (value) => {
    const intensity = value / maxValue;
    const blue = Math.round(255 - intensity * 200);
    return `rgb(59, ${blue}, 246)`;
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Confusion Matrix
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Shows how often the AI confuses one category for another
      </p>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr>
              <th className="border border-gray-300 p-2 bg-gray-50 text-xs font-semibold">
                Actual \ Predicted
              </th>
              {labels.map((label, idx) => (
                <th
                  key={idx}
                  className="border border-gray-300 p-2 bg-gray-50 text-xs font-semibold transform -rotate-45 h-24"
                  style={{ minWidth: '60px' }}
                >
                  <div className="transform rotate-45 origin-center">
                    {label}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, rowIdx) => (
              <tr key={rowIdx}>
                <td className="border border-gray-300 p-2 bg-gray-50 text-xs font-semibold">
                  {labels[rowIdx]}
                </td>
                {row.map((value, colIdx) => {
                  const isCorrect = rowIdx === colIdx;
                  return (
                    <td
                      key={colIdx}
                      className="border border-gray-300 p-2 text-center text-xs font-semibold cursor-pointer hover:opacity-80 transition-opacity"
                      style={{
                        backgroundColor: getColor(value),
                        color: value > maxValue * 0.5 ? 'white' : 'black'
                      }}
                      title={`Actual: ${labels[rowIdx]}, Predicted: ${labels[colIdx]}, Count: ${value}`}
                    >
                      {value}
                      {isCorrect && value > 0 && (
                        <div className="text-green-400 text-lg">✓</div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-100 border border-gray-300"></div>
          <span>Low</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-400 border border-gray-300"></div>
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-600 border border-gray-300"></div>
          <span>High</span>
        </div>
        <span className="ml-4 text-gray-600">
          Diagonal = Correct Predictions
        </span>
      </div>
    </div>
  );
};

export default ConfusionMatrix;
