import React, { useState, useEffect } from 'react';
import Card, { CardContent } from './enhanced/Card';
import Button from './enhanced/Button';
import { detectKnowledgeGaps } from '../api/gaps';
import { AlertTriangle, Lightbulb, TrendingUp, HelpCircle } from 'lucide-react';

const SearchWithGaps = ({ searchQuery, searchResults }) => {
  const [gapAnalysis, setGapAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (searchQuery && searchQuery.length > 3) {
      analyzeQueryGaps();
    }
  }, [searchQuery]);

  const analyzeQueryGaps = async () => {
    setLoading(true);
    try {
      const response = await detectKnowledgeGaps({
        query: searchQuery,
        threshold: 0.5
      });
      setGapAnalysis(response);
    } catch (error) {
      console.error('Error analyzing gaps:', error);
    }
    setLoading(false);
  };

  if (!searchQuery || !gapAnalysis) return null;

  const { coverage_score, top_gaps, research_opportunities } = gapAnalysis;
  const hasSignificantGaps = coverage_score < 0.5 || top_gaps?.length > 0;

  return (
    <Card className="mb-4 border-orange-200 bg-orange-50">
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              <h4 className="font-semibold text-orange-900">Knowledge Gap Analysis</h4>
            </div>

            {loading ? (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                <span>Analyzing research coverage...</span>
              </div>
            ) : (
              <>
                {/* Coverage Summary */}
                <div className="mb-3">
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-gray-700">Research Coverage:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${
                            coverage_score > 0.7 ? 'bg-green-500' :
                            coverage_score > 0.4 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${coverage_score * 100}%` }}
                        />
                      </div>
                      <span className="font-medium">
                        {(coverage_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Quick Insights */}
                {hasSignificantGaps && (
                  <div className="space-y-2 mb-3">
                    {top_gaps?.slice(0, 3).map((gap, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-sm">
                        <span className="text-orange-600 mt-0.5">•</span>
                        <div>
                          <span className="font-medium">{gap.area || gap.type}:</span>
                          <span className="text-gray-600 ml-1">
                            {gap.description || `Only ${gap.current_coverage || 0} documents found`}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Research Opportunities */}
                {research_opportunities?.length > 0 && (
                  <div className="border-t border-orange-200 pt-3 mt-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Lightbulb className="w-4 h-4 text-amber-600" />
                      <span className="font-medium text-sm">Research Opportunities:</span>
                    </div>
                    <div className="space-y-1">
                      {research_opportunities.slice(0, 2).map((opp, idx) => (
                        <div key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                          <TrendingUp className="w-3 h-3 text-green-600 mt-1 flex-shrink-0" />
                          <span>{opp.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggestions for Better Results */}
                {coverage_score < 0.3 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mt-3">
                    <div className="flex items-start gap-2">
                      <HelpCircle className="w-4 h-4 text-blue-600 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-medium text-blue-900 mb-1">
                          Limited coverage detected
                        </p>
                        <p className="text-blue-700">
                          This area appears to be under-researched. Consider:
                        </p>
                        <ul className="mt-1 ml-4 list-disc text-blue-600">
                          <li>Broadening your search terms</li>
                          <li>Exploring related research areas</li>
                          <li>Contributing new research to fill these gaps</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Action Button */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowDetails(!showDetails)}
            className="ml-4"
          >
            {showDetails ? 'Hide' : 'View'} Details
          </Button>
        </div>

        {/* Detailed Analysis (Expandable) */}
        {showDetails && gapAnalysis && (
          <div className="mt-4 pt-4 border-t border-orange-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Research Areas */}
              {gapAnalysis.research_areas?.areas && (
                <div>
                  <h5 className="font-medium mb-2">Research Area Distribution:</h5>
                  <div className="space-y-1">
                    {Object.entries(gapAnalysis.research_areas.areas)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 5)
                      .map(([area, count]) => (
                        <div key={area} className="flex justify-between text-sm">
                          <span className="text-gray-600">{area}</span>
                          <span className="font-medium">{count} docs</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Summary Stats */}
              <div>
                <h5 className="font-medium mb-2">Coverage Summary:</h5>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Documents:</span>
                    <span className="font-medium">{gapAnalysis.summary?.total_documents || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Research Areas:</span>
                    <span className="font-medium">{gapAnalysis.summary?.total_areas || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Identified Gaps:</span>
                    <span className="font-medium text-orange-600">
                      {top_gaps?.length || 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* All Gaps */}
            {top_gaps?.length > 3 && (
              <div className="mt-4">
                <h5 className="font-medium mb-2">All Identified Gaps:</h5>
                <div className="max-h-40 overflow-y-auto space-y-2">
                  {top_gaps.slice(3).map((gap, idx) => (
                    <div key={idx} className="text-sm p-2 bg-white rounded border">
                      <span className="font-medium">{gap.area || gap.type}:</span>
                      <span className="text-gray-600 ml-1">
                        {gap.gap_severity === 'high' && (
                          <span className="text-red-600">[High Priority] </span>
                        )}
                        {gap.description || `Coverage: ${gap.current_coverage || 0}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SearchWithGaps;