import { useState, useEffect } from 'react';
import { getFeedbackThemes, getFeedbackAnalyses, getSystemFeedbackStats } from '../api/feedback';

const FeedbackAnalyticsDashboard = () => {
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [feedbackThemes, setFeedbackThemes] = useState([]);
  const [feedbackAnalyses, setFeedbackAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch all data in parallel
        const [statsRes, themesRes, analysesRes] = await Promise.all([
          getSystemFeedbackStats(),
          getFeedbackThemes(),
          getFeedbackAnalyses()
        ]);
        
        setFeedbackStats(statsRes);
        setFeedbackThemes(themesRes);
        setFeedbackAnalyses(analysesRes);
        setError(null);
      } catch (err) {
        console.error('Error fetching feedback analytics data:', err);
        setError('Failed to load feedback analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const renderTrendChart = () => {
    if (!feedbackStats || !feedbackStats.trends) return null;
    
    const trend = feedbackStats.trends;
    const maxValue = Math.max(...Object.values(trend).map(t => Math.max(t.positive || 0, t.negative || 0, t.neutral || 0)));
    
    return (
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-4">Feedback Trends</h3>
        <div className="h-64">
          {Object.keys(trend).map((date, i) => (
            <div key={date} className="flex items-end h-48 mb-1">
              <div className="text-xs text-right mr-2 w-20 text-gray-500">
                {date}
              </div>
              <div 
                className="bg-green-500 mr-1" 
                style={{ 
                  height: `${((trend[date].positive || 0) / maxValue) * 100}%`,
                  width: '30px'
                }}
                title={`Positive: ${trend[date].positive || 0}`}
              />
              <div 
                className="bg-gray-400 mr-1" 
                style={{ 
                  height: `${((trend[date].neutral || 0) / maxValue) * 100}%`,
                  width: '30px'
                }}
                title={`Neutral: ${trend[date].neutral || 0}`}
              />
              <div 
                className="bg-red-500" 
                style={{ 
                  height: `${((trend[date].negative || 0) / maxValue) * 100}%`,
                  width: '30px'
                }}
                title={`Negative: ${trend[date].negative || 0}`}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-center mt-2">
          <div className="flex items-center mr-4">
            <div className="w-3 h-3 bg-green-500 mr-1 rounded-sm"></div>
            <span className="text-xs text-gray-600">Positive</span>
          </div>
          <div className="flex items-center mr-4">
            <div className="w-3 h-3 bg-gray-400 mr-1 rounded-sm"></div>
            <span className="text-xs text-gray-600">Neutral</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 mr-1 rounded-sm"></div>
            <span className="text-xs text-gray-600">Negative</span>
          </div>
        </div>
      </div>
    );
  };

  const renderOverviewTab = () => {
    if (!feedbackStats) return null;
    
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm font-medium mb-2">Total Feedback</h3>
            <p className="text-3xl font-bold">{feedbackStats.total_count || 0}</p>
            {feedbackStats.total_change && (
              <p className={`text-sm ${feedbackStats.total_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {feedbackStats.total_change > 0 ? '+' : ''}{feedbackStats.total_change}% from last period
              </p>
            )}
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm font-medium mb-2">Satisfaction Rate</h3>
            <p className="text-3xl font-bold">
              {feedbackStats.positive_count && feedbackStats.total_count 
                ? `${Math.round((feedbackStats.positive_count / feedbackStats.total_count) * 100)}%` 
                : '0%'}
            </p>
            {feedbackStats.satisfaction_change && (
              <p className={`text-sm ${feedbackStats.satisfaction_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {feedbackStats.satisfaction_change > 0 ? '+' : ''}{feedbackStats.satisfaction_change}% from last period
              </p>
            )}
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm font-medium mb-2">Feedback Rate</h3>
            <p className="text-3xl font-bold">
              {feedbackStats.feedback_rate ? `${Math.round(feedbackStats.feedback_rate * 100)}%` : '0%'}
            </p>
            <p className="text-sm text-gray-500">of total queries</p>
          </div>
        </div>
        
        {renderTrendChart()}
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Top Issues</h3>
          {feedbackStats.common_issues && feedbackStats.common_issues.length > 0 ? (
            <div className="space-y-3">
              {feedbackStats.common_issues.slice(0, 5).map((issue, i) => (
                <div key={i} className="flex items-center">
                  <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full" 
                      style={{ width: `${(issue.count / feedbackStats.common_issues[0].count) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between w-full">
                    <span className="text-sm text-gray-700">{issue.name}</span>
                    <span className="text-sm text-gray-500">{issue.count}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No issues reported yet</p>
          )}
        </div>
      </div>
    );
  };
  
  const renderThemesTab = () => {
    if (!feedbackThemes || feedbackThemes.length === 0) {
      return (
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <p className="text-gray-500">No feedback themes identified yet.</p>
        </div>
      );
    }
    
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Theme
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Priority
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Feedback Count
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Reported
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {feedbackThemes.map((theme) => (
              <tr key={theme.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{theme.title}</div>
                  <div className="text-sm text-gray-500">{theme.description}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${theme.priority === 'critical' ? 'bg-red-100 text-red-800' : 
                      theme.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                      theme.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'}`}>
                    {theme.priority}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${theme.status === 'active' ? 'bg-gray-100 text-gray-800' : 
                      theme.status === 'investigating' ? 'bg-blue-100 text-blue-800' :
                      theme.status === 'implementing' ? 'bg-purple-100 text-purple-800' :
                      theme.status === 'resolved' ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'}`}>
                    {theme.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {theme.feedback_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(theme.last_reported).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };
  
  const renderAnalysesTab = () => {
    if (!feedbackAnalyses || feedbackAnalyses.length === 0) {
      return (
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <p className="text-gray-500">No feedback analyses available yet.</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {feedbackAnalyses.map((analysis) => (
          <div key={analysis.analysis_id} className="bg-white p-4 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">
                Analysis: {new Date(analysis.analysis_date).toLocaleDateString()}
              </h3>
              <span className="text-sm text-gray-500">
                {analysis.total_feedback_analyzed} feedback items
              </span>
            </div>
            
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Period Analyzed</h4>
              <p className="text-sm text-gray-600">
                {new Date(analysis.date_range_start).toLocaleDateString()} to {new Date(analysis.date_range_end).toLocaleDateString()}
              </p>
            </div>
            
            {analysis.improvement_opportunities && analysis.improvement_opportunities.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Improvement Opportunities</h4>
                <ul className="list-disc list-inside text-sm text-gray-600">
                  {analysis.improvement_opportunities.slice(0, 3).map((opportunity, i) => (
                    <li key={i}>{opportunity}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {analysis.recommended_actions && analysis.recommended_actions.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Recommended Actions</h4>
                <ul className="list-disc list-inside text-sm text-gray-600">
                  {analysis.recommended_actions.slice(0, 3).map((action, i) => (
                    <li key={i}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-pulse text-gray-600">Loading analytics data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 p-6 rounded-lg">
      <h2 className="text-2xl font-bold mb-6">Feedback Analytics Dashboard</h2>
      
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('themes')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'themes'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Feedback Themes
            </button>
            <button
              onClick={() => setActiveTab('analyses')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analyses'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Analyses
            </button>
          </nav>
        </div>
      </div>
      
      <div>
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'themes' && renderThemesTab()}
        {activeTab === 'analyses' && renderAnalysesTab()}
      </div>
    </div>
  );
};

export default FeedbackAnalyticsDashboard;