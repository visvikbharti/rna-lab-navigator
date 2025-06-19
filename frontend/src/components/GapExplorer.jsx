import React, { useState, useEffect } from 'react';
import Card, { CardContent, CardHeader, CardTitle } from './enhanced/Card';
import Button from './enhanced/Button';
import { detectKnowledgeGaps, getGapAnalysis, suggestResearchQuestions } from '../api/gaps';
import { 
  AlertCircle, 
  Lightbulb, 
  Filter, 
  ChevronRight, 
  Clock,
  Users,
  DollarSign,
  Target,
  BookOpen,
  FlaskConical,
  HelpCircle,
  Layers
} from 'lucide-react';

const GapExplorer = ({ onSelectGap }) => {
  const [loading, setLoading] = useState(false);
  const [gaps, setGaps] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [selectedGap, setSelectedGap] = useState(null);
  const [gapDetails, setGapDetails] = useState(null);
  const [filters, setFilters] = useState({
    gap_type: '',
    min_severity: 'low',
    domain: ''
  });
  const [activeTab, setActiveTab] = useState('gaps');

  useEffect(() => {
    fetchGaps();
  }, [filters]);

  const fetchGaps = async () => {
    setLoading(true);
    try {
      const response = await detectKnowledgeGaps(filters);
      setGaps(response.gaps || []);
    } catch (error) {
      console.error('Error fetching gaps:', error);
    }
    setLoading(false);
  };

  const fetchOpportunities = async () => {
    setLoading(true);
    try {
      const response = await suggestResearchQuestions({ gaps: gaps.slice(0, 10), context: filters.domain });
      setOpportunities(response.opportunities || []);
    } catch (error) {
      console.error('Error fetching opportunities:', error);
    }
    setLoading(false);
  };

  const handleGapClick = async (gap, index) => {
    setSelectedGap(gap);
    
    // Fetch detailed information
    try {
      const gapId = `${gap.gap_type}_${index}`;
      const details = await getGapAnalysis(gap.gap_type);
      setGapDetails(details);
    } catch (error) {
      console.error('Error fetching gap details:', error);
    }

    if (onSelectGap) {
      onSelectGap(gap);
    }
  };

  const getGapIcon = (gapType) => {
    const icons = {
      coverage: <Layers className="w-5 h-5" />,
      validation: <FlaskConical className="w-5 h-5" />,
      question: <HelpCircle className="w-5 h-5" />,
      combination: <Target className="w-5 h-5" />
    };
    return icons[gapType] || <AlertCircle className="w-5 h-5" />;
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'text-blue-600 bg-blue-50',
      medium: 'text-yellow-600 bg-yellow-50',
      high: 'text-red-600 bg-red-50'
    };
    return colors[severity] || colors.medium;
  };

  const renderGapCard = (gap, index) => (
    <div
      key={index}
      className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => handleGapClick(gap, index)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {getGapIcon(gap.gap_type)}
          <span className={`text-xs px-2 py-1 rounded-full ${getSeverityColor(gap.gap_severity)}`}>
            {gap.gap_severity}
          </span>
        </div>
        {gap.impact_score && (
          <span className="text-sm text-gray-500">
            Impact: {(gap.impact_score * 100).toFixed(0)}%
          </span>
        )}
      </div>
      
      <h4 className="font-semibold mb-1">{gap.title}</h4>
      <p className="text-sm text-gray-600 line-clamp-2">{gap.description}</p>
      
      {gap.source && (
        <p className="text-xs text-gray-500 mt-2">Source: {gap.source}</p>
      )}
    </div>
  );

  const renderOpportunityCard = (opportunity, index) => (
    <div
      key={index}
      className="border rounded-lg p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-amber-500" />
          <span className={`text-xs px-2 py-1 rounded-full ${
            opportunity.difficulty === 'low' ? 'bg-green-50 text-green-600' :
            opportunity.difficulty === 'medium' ? 'bg-yellow-50 text-yellow-600' :
            'bg-red-50 text-red-600'
          }`}>
            {opportunity.difficulty} difficulty
          </span>
        </div>
        <span className="text-sm font-semibold text-green-600">
          {(opportunity.feasibility_score * 100).toFixed(0)}% feasible
        </span>
      </div>
      
      <h4 className="font-semibold mb-1">{opportunity.title}</h4>
      <p className="text-sm text-gray-600 mb-3">{opportunity.description}</p>
      
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{opportunity.estimated_timeline}</span>
        </div>
        <div className="flex items-center gap-1">
          <Target className="w-3 h-3" />
          <span>Impact: {(opportunity.impact_score * 100).toFixed(0)}%</span>
        </div>
      </div>

      {opportunity.potential_collaborators?.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs font-medium mb-1">Suggested Collaborators:</p>
          <div className="flex gap-2 flex-wrap">
            {opportunity.potential_collaborators.map((collab, idx) => (
              <span key={idx} className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded">
                {collab.expertise}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="w-6 h-6" />
          Knowledge Gap Explorer
        </CardTitle>
        
        {/* Tabs */}
        <div className="flex gap-2 mt-4">
          <Button
            variant={activeTab === 'gaps' ? 'default' : 'outline'}
            onClick={() => {
              setActiveTab('gaps');
              fetchGaps();
            }}
          >
            Knowledge Gaps
          </Button>
          <Button
            variant={activeTab === 'opportunities' ? 'default' : 'outline'}
            onClick={() => {
              setActiveTab('opportunities');
              fetchOpportunities();
            }}
          >
            Research Opportunities
          </Button>
        </div>

        {/* Filters (for gaps tab) */}
        {activeTab === 'gaps' && (
          <div className="mt-4 flex gap-2 flex-wrap">
            <select
              value={filters.gap_type}
              onChange={(e) => setFilters({ ...filters, gap_type: e.target.value })}
              className="px-3 py-2 border rounded-md text-sm"
            >
              <option value="">All Types</option>
              <option value="coverage">Coverage Gaps</option>
              <option value="validation">Missing Validations</option>
              <option value="question">Unanswered Questions</option>
              <option value="combination">Unexplored Combinations</option>
            </select>
            
            <select
              value={filters.min_severity}
              onChange={(e) => setFilters({ ...filters, min_severity: e.target.value })}
              className="px-3 py-2 border rounded-md text-sm"
            >
              <option value="low">All Severities</option>
              <option value="medium">Medium & High</option>
              <option value="high">High Only</option>
            </select>
            
            <input
              type="text"
              placeholder="Filter by domain..."
              value={filters.domain}
              onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
              className="px-3 py-2 border rounded-md text-sm flex-1"
            />
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Gap/Opportunity List */}
          <div className="space-y-4">
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : activeTab === 'gaps' ? (
              gaps.length > 0 ? (
                gaps.map((gap, index) => renderGapCard(gap, index))
              ) : (
                <p className="text-gray-500 text-center py-8">No gaps found with current filters</p>
              )
            ) : (
              opportunities.length > 0 ? (
                opportunities.map((opp, index) => renderOpportunityCard(opp, index))
              ) : (
                <p className="text-gray-500 text-center py-8">No opportunities found</p>
              )
            )}
          </div>

          {/* Details Panel */}
          {(selectedGap || gapDetails) && activeTab === 'gaps' && (
            <div className="border rounded-lg p-6 bg-gray-50">
              <h3 className="font-semibold text-lg mb-4">Gap Details</h3>
              
              {gapDetails ? (
                <div className="space-y-4">
                  {/* Basic Info */}
                  <div>
                    <h4 className="font-medium mb-2">{gapDetails.title || gapDetails.claim || gapDetails.question}</h4>
                    <p className="text-sm text-gray-600">{gapDetails.description || gapDetails.context}</p>
                  </div>

                  {/* Validation Methods */}
                  {gapDetails.validation_methods && (
                    <div>
                      <h5 className="font-medium mb-1">Suggested Validation Methods:</h5>
                      <ul className="list-disc list-inside text-sm text-gray-600">
                        {gapDetails.validation_methods.map((method, idx) => (
                          <li key={idx}>{method}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Potential Approaches */}
                  {gapDetails.potential_approaches && (
                    <div>
                      <h5 className="font-medium mb-1">Potential Approaches:</h5>
                      <ul className="list-disc list-inside text-sm text-gray-600">
                        {gapDetails.potential_approaches.map((approach, idx) => (
                          <li key={idx}>{approach}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Research Plan */}
                  {gapDetails.research_plan && (
                    <div>
                      <h5 className="font-medium mb-2">Research Plan:</h5>
                      <div className="space-y-2">
                        {gapDetails.research_plan.phases.map((phase) => (
                          <div key={phase.phase} className="border-l-4 border-blue-400 pl-3">
                            <h6 className="font-medium text-sm">
                              Phase {phase.phase}: {phase.name}
                            </h6>
                            <p className="text-xs text-gray-500">{phase.duration}</p>
                            <ul className="text-xs text-gray-600 mt-1">
                              {phase.activities.map((activity, idx) => (
                                <li key={idx}>• {activity}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Related Work */}
                  {(gapDetails.related_work || gapDetails.related_papers) && (
                    <div>
                      <h5 className="font-medium mb-1">Related Work:</h5>
                      <div className="space-y-1">
                        {(gapDetails.related_work || gapDetails.related_papers || []).map((paper, idx) => (
                          <div key={idx} className="text-sm">
                            <span className="text-blue-600">{paper.title}</span>
                            {paper.relevance && (
                              <span className="text-xs text-gray-500 ml-2">
                                (Relevance: {(paper.relevance * 100).toFixed(0)}%)
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Button */}
                  <div className="pt-4">
                    <Button className="w-full">
                      <BookOpen className="w-4 h-4 mr-2" />
                      Start Research on This Gap
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-500">Loading details...</p>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default GapExplorer;