import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  SparklesIcon,
  DocumentIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ArrowTopRightOnSquareIcon,
  ClipboardDocumentCheckIcon
} from '@heroicons/react/24/outline';

function InsightCard({ insight, validation, onValidate, onSelect, isValidating }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyInsight = () => {
    const text = `
${insight.title}

${insight.description}

Evidence:
${insight.evidence_snippets.map((e, i) => `${i + 1}. ${e}`).join('\n')}

Impact: ${insight.potential_impact}

Suggested Actions:
${insight.suggested_actions.map((a, i) => `- ${a}`).join('\n')}
    `.trim();

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getNoveltyLabel = (score) => {
    if (score >= 0.8) return 'Highly Novel';
    if (score >= 0.6) return 'Moderately Novel';
    return 'Low Novelty';
  };

  return (
    <motion.div
      layout
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 pb-3">
        <div className="flex items-start justify-between mb-3">
          <h3 
            className="text-lg font-semibold text-gray-900 dark:text-white cursor-pointer hover:text-indigo-600 dark:hover:text-indigo-400 line-clamp-2"
            onClick={() => onSelect && onSelect()}
          >
            {insight.title}
          </h3>
          <button
            onClick={copyInsight}
            className="ml-2 p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            title="Copy insight"
          >
            {copied ? (
              <CheckCircleIcon className="w-5 h-5 text-green-600" />
            ) : (
              <ClipboardDocumentCheckIcon className="w-5 h-5" />
            )}
          </button>
        </div>

        <p className="text-gray-700 dark:text-gray-300 text-sm mb-4 line-clamp-3">
          {insight.description}
        </p>

        {/* Metrics */}
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-1">
            <span className={`font-medium ${getConfidenceColor(insight.confidence_score)}`}>
              {(insight.confidence_score * 100).toFixed(0)}%
            </span>
            <span className="text-gray-500 dark:text-gray-400">confidence</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <SparklesIcon className="w-4 h-4 text-purple-500" />
            <span className="text-gray-700 dark:text-gray-300">
              {getNoveltyLabel(insight.novelty_score)}
            </span>
          </div>

          <div className="flex items-center space-x-1">
            <DocumentIcon className="w-4 h-4 text-gray-500" />
            <span className="text-gray-700 dark:text-gray-300">
              {insight.papers_involved.length} papers
            </span>
          </div>
        </div>

        {/* Validation Status */}
        {validation && (
          <div className="mt-3 flex items-center space-x-2">
            {validation.is_valid ? (
              <>
                <CheckCircleIcon className="w-5 h-5 text-green-600" />
                <span className="text-sm text-green-600 dark:text-green-400">
                  Validated ({(validation.confidence_score * 100).toFixed(0)}% confidence)
                </span>
              </>
            ) : (
              <>
                <XCircleIcon className="w-5 h-5 text-red-600" />
                <span className="text-sm text-red-600 dark:text-red-400">
                  Validation failed
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Expand/Collapse Button */}
      <div className="px-4 pb-2">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center space-x-2 text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300"
        >
          {expanded ? (
            <>
              <ChevronUpIcon className="w-4 h-4" />
              <span>Show less</span>
            </>
          ) : (
            <>
              <ChevronDownIcon className="w-4 h-4" />
              <span>Show evidence & actions</span>
            </>
          )}
        </button>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="border-t border-gray-200 dark:border-gray-700"
        >
          <div className="p-4 space-y-4">
            {/* Evidence */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Evidence
              </h4>
              <ul className="space-y-2">
                {insight.evidence_snippets.map((evidence, index) => (
                  <li key={index} className="text-sm text-gray-700 dark:text-gray-300">
                    <span className="inline-block w-5 h-5 rounded-full bg-gray-200 dark:bg-gray-700 text-xs text-center leading-5 mr-2">
                      {index + 1}
                    </span>
                    {evidence}
                  </li>
                ))}
              </ul>
            </div>

            {/* Impact */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Potential Impact
              </h4>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {insight.potential_impact}
              </p>
            </div>

            {/* Suggested Actions */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Suggested Actions
              </h4>
              <ul className="space-y-1">
                {insight.suggested_actions.map((action, index) => (
                  <li key={index} className="flex items-start space-x-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="text-indigo-500 mt-0.5">•</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Papers */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Related Papers
              </h4>
              <div className="flex flex-wrap gap-2">
                {insight.papers_involved.map((paperId, index) => (
                  <button
                    key={index}
                    onClick={() => onSelect && onSelect(paperId)}
                    className="inline-flex items-center space-x-1 px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  >
                    <DocumentIcon className="w-3 h-3" />
                    <span>Paper {index + 1}</span>
                    <ArrowTopRightOnSquareIcon className="w-3 h-3" />
                  </button>
                ))}
              </div>
            </div>

            {/* Validation */}
            {validation && validation.reasoning && (
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                  Validation Details
                </h4>
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                  {validation.reasoning}
                </p>
                {validation.suggested_improvements.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Suggested Improvements:
                    </p>
                    <ul className="space-y-1">
                      {validation.suggested_improvements.map((improvement, index) => (
                        <li key={index} className="text-sm text-gray-600 dark:text-gray-400">
                          • {improvement}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="px-4 pb-4 flex space-x-2">
            {!validation && (
              <button
                onClick={onValidate}
                disabled={isValidating}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
              >
                {isValidating ? 'Validating...' : 'Validate Insight'}
              </button>
            )}
            
            <button
              onClick={() => onSelect && onSelect()}
              className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
            >
              View Details
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default InsightCard;