import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LightBulbIcon,
  LinkIcon,
  BeakerIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  DocumentDuplicateIcon,
  ChartBarIcon,
  SparklesIcon,
  ArrowsRightLeftIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { generateCrossPaperInsights, validateConnection } from '../api/intelligence';
import InsightCard from './InsightCard';
import ResearchConnectionGraph from './ResearchConnectionGraph';
import Loading from './enhanced/Loading';

const insightTypeIcons = {
  complementary_methods: <BeakerIcon className="w-5 h-5" />,
  contradictory_findings: <ExclamationTriangleIcon className="w-5 h-5" />,
  method_transfer: <ArrowsRightLeftIcon className="w-5 h-5" />,
  missing_citation: <LinkIcon className="w-5 h-5" />,
  converging_trend: <ArrowTrendingUpIcon className="w-5 h-5" />
};

const insightTypeColors = {
  complementary_methods: 'bg-blue-500',
  contradictory_findings: 'bg-red-500',
  method_transfer: 'bg-purple-500',
  missing_citation: 'bg-yellow-500',
  converging_trend: 'bg-green-500'
};

function CrossPaperInsights({ query, papers, onInsightSelect }) {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [minConfidence, setMinConfidence] = useState(0.6);
  const [showGraph, setShowGraph] = useState(false);
  const [validatingInsight, setValidatingInsight] = useState(null);
  const [validationResults, setValidationResults] = useState({});

  useEffect(() => {
    if (query || (papers && papers.length > 0)) {
      loadInsights();
    }
  }, [query, papers, selectedTypes, minConfidence]);

  const loadInsights = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await generateCrossPaperInsights({
        query,
        paper_ids: papers?.map(p => p.doc_id) || [],
        insight_types: selectedTypes.length > 0 ? selectedTypes : null,
        min_confidence: minConfidence
      });

      setInsights(response.insights || []);
    } catch (err) {
      console.error('Error loading insights:', err);
      setError('Failed to generate insights. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTypeToggle = (type) => {
    setSelectedTypes(prev => 
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const validateInsight = async (insight) => {
    setValidatingInsight(insight);
    
    try {
      const result = await validateConnection({ insight });
      setValidationResults(prev => ({
        ...prev,
        [insight.title]: result
      }));
    } catch (err) {
      console.error('Error validating insight:', err);
    } finally {
      setValidatingInsight(null);
    }
  };

  const getInsightsByType = () => {
    const grouped = {};
    insights.forEach(insight => {
      if (!grouped[insight.insight_type]) {
        grouped[insight.insight_type] = [];
      }
      grouped[insight.insight_type].push(insight);
    });
    return grouped;
  };

  const insightTypes = [
    { id: 'complementary', label: 'Complementary Methods', icon: insightTypeIcons.complementary_methods },
    { id: 'contradictory', label: 'Contradictory Findings', icon: insightTypeIcons.contradictory_findings },
    { id: 'methodological', label: 'Method Transfers', icon: insightTypeIcons.method_transfer },
    { id: 'missing_citations', label: 'Missing Citations', icon: insightTypeIcons.missing_citation },
    { id: 'converging_trends', label: 'Converging Trends', icon: insightTypeIcons.converging_trend }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg">
            <SparklesIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Cross-Paper Insights
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Discover hidden connections and "aha!" moments
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowGraph(!showGraph)}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <ChartBarIcon className="w-5 h-5" />
          <span>{showGraph ? 'Hide' : 'Show'} Connection Graph</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Insight Types
          </h3>
          <div className="flex flex-wrap gap-2">
            {insightTypes.map(type => (
              <button
                key={type.id}
                onClick={() => handleTypeToggle(type.id)}
                className={`
                  flex items-center space-x-2 px-3 py-1.5 rounded-full text-sm
                  transition-all duration-200
                  ${selectedTypes.includes(type.id)
                    ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 ring-2 ring-indigo-500'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }
                `}
              >
                {type.icon}
                <span>{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Minimum Confidence: {minConfidence.toFixed(1)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={minConfidence}
            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
            className="w-full mt-2"
          />
        </div>
      </div>

      {/* Connection Graph */}
      <AnimatePresence>
        {showGraph && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <ResearchConnectionGraph
              papers={papers}
              insights={insights}
              onNodeClick={(paperId) => {
                const paper = papers.find(p => p.doc_id === paperId);
                if (paper && onInsightSelect) {
                  onInsightSelect(paper);
                }
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center py-12">
          <Loading message="Discovering insights..." />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Insights by Type */}
      {!loading && insights.length > 0 && (
        <div className="space-y-8">
          {Object.entries(getInsightsByType()).map(([type, typeInsights]) => (
            <div key={type} className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${insightTypeColors[type]}`}>
                  {insightTypeIcons[type]}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                  {type.replace(/_/g, ' ')}
                </h3>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  ({typeInsights.length} insights)
                </span>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {typeInsights.map((insight, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <InsightCard
                      insight={insight}
                      validation={validationResults[insight.title]}
                      onValidate={() => validateInsight(insight)}
                      onSelect={() => onInsightSelect && onInsightSelect(insight)}
                      isValidating={validatingInsight?.title === insight.title}
                    />
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Insights State */}
      {!loading && insights.length === 0 && (
        <div className="text-center py-12">
          <LightBulbIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            No insights found. Try adjusting your filters or search query.
          </p>
        </div>
      )}

      {/* Stats Footer */}
      {insights.length > 0 && (
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                {insights.length}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Insights</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {insights.filter(i => i.novelty_score > 0.8).length}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">High Novelty</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {insights.filter(i => i.confidence_score > 0.8).length}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">High Confidence</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {new Set(insights.flatMap(i => i.papers_involved)).size}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Papers Connected</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CrossPaperInsights;