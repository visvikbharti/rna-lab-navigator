import { useState, useEffect } from 'react';
import { 
  getSearchQualitySummary, 
  getQualityByDocType, 
  getQualityByRankingProfile,
  getRerankingImpact,
  getSearchIssues,
  getSearchPerformanceOverTime
} from '../api/search-quality';

const SearchQualityDashboard = () => {
  // State for different metrics
  const [summary, setSummary] = useState(null);
  const [docTypeMetrics, setDocTypeMetrics] = useState(null);
  const [profileMetrics, setProfileMetrics] = useState(null);
  const [rerankingImpact, setRerankingImpact] = useState(null);
  const [searchIssues, setSearchIssues] = useState(null);
  const [performanceOverTime, setPerformanceOverTime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState(30);
  const [timeInterval, setTimeInterval] = useState('day');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch all data in parallel
        const [
          summaryRes, 
          docTypeRes, 
          profileRes, 
          rerankingRes, 
          issuesRes, 
          performanceRes
        ] = await Promise.all([
          getSearchQualitySummary(),
          getQualityByDocType(),
          getQualityByRankingProfile(),
          getRerankingImpact(),
          getSearchIssues(),
          getSearchPerformanceOverTime({ days: timeRange, interval: timeInterval })
        ]);
        
        setSummary(summaryRes);
        setDocTypeMetrics(docTypeRes);
        setProfileMetrics(profileRes);
        setRerankingImpact(rerankingRes);
        setSearchIssues(issuesRes);
        setPerformanceOverTime(performanceRes);
        setError(null);
      } catch (err) {
        console.error('Error fetching search quality data:', err);
        setError('Failed to load search quality data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange, timeInterval]);

  // Refresh performance data when time range changes
  const handleTimeRangeChange = async (days, interval) => {
    setTimeRange(days);
    setTimeInterval(interval || timeInterval);
    try {
      const performanceRes = await getSearchPerformanceOverTime({ 
        days, 
        interval: interval || timeInterval 
      });
      setPerformanceOverTime(performanceRes);
    } catch (err) {
      console.error('Error updating performance data:', err);
    }
  };

  const renderOverviewTab = () => {
    if (!summary) return null;
    
    const { search_metrics, feedback_metrics } = summary;
    
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm font-medium mb-2">Total Searches</h3>
            <p className="text-3xl font-bold">{search_metrics?.total_searches || 0}</p>
            <p className="text-sm text-gray-500">{search_metrics?.recent_searches || 0} in last week</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm font-medium mb-2">Satisfaction Rate</h3>
            <p className="text-3xl font-bold">
              {feedback_metrics?.satisfaction_rate 
                ? `${Math.round(feedback_metrics.satisfaction_rate * 100)}%` 
                : '0%'}
            </p>
            {feedback_metrics?.satisfaction_change && (
              <p className={`text-sm ${feedback_metrics.satisfaction_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {feedback_metrics.satisfaction_change > 0 ? '+' : ''}{Math.round(feedback_metrics.satisfaction_change)}% from last period
              </p>
            )}
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm font-medium mb-2">Feedback Rate</h3>
            <p className="text-3xl font-bold">
              {feedback_metrics?.feedback_rate 
                ? `${Math.round(feedback_metrics.feedback_rate * 100)}%` 
                : '0%'}
            </p>
            <p className="text-sm text-gray-500">of total searches</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm font-medium mb-2">Avg Search Time</h3>
            <p className="text-3xl font-bold">
              {search_metrics?.avg_search_time_ms 
                ? `${Math.round(search_metrics.avg_search_time_ms)}ms` 
                : 'N/A'}
            </p>
            <p className="text-sm text-gray-500">includes retrieval + reranking</p>
          </div>
        </div>
        
        {/* Quality ratings */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Search Quality Ratings</h3>
          {feedback_metrics?.rating_metrics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(feedback_metrics.rating_metrics).map(([key, value]) => (
                value && (
                  <div key={key} className="bg-gray-50 p-3 rounded-lg">
                    <h4 className="text-sm text-gray-700 capitalize mb-2">
                      {key.replace('_', ' ')}
                    </h4>
                    <div className="flex items-center">
                      <div className="flex text-yellow-400 mr-2">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <span key={i} className="text-lg">
                            {i < Math.round(value) ? '★' : '☆'}
                          </span>
                        ))}
                      </div>
                      <span className="text-gray-700">
                        ({value.toFixed(1)})
                      </span>
                    </div>
                  </div>
                )
              ))}
            </div>
          )}
        </div>
        
        {/* Reranking impact */}
        {rerankingImpact && rerankingImpact.with_reranking && rerankingImpact.without_reranking && (
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Reranking Impact</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-gray-200 rounded-lg p-3">
                <h4 className="text-sm font-medium text-gray-700 mb-2">With Reranking</h4>
                <div className="space-y-2">
                  <p className="flex justify-between">
                    <span className="text-gray-600">Searches:</span>
                    <span className="font-medium">{rerankingImpact.with_reranking.search_count}</span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-gray-600">Satisfaction:</span>
                    <span className="font-medium">
                      {Math.round(rerankingImpact.with_reranking.satisfaction_rate * 100)}%
                    </span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-gray-600">Avg Time:</span>
                    <span className="font-medium">
                      {Math.round(rerankingImpact.with_reranking.avg_search_time)}ms
                    </span>
                  </p>
                </div>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-3">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Without Reranking</h4>
                <div className="space-y-2">
                  <p className="flex justify-between">
                    <span className="text-gray-600">Searches:</span>
                    <span className="font-medium">{rerankingImpact.without_reranking.search_count}</span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-gray-600">Satisfaction:</span>
                    <span className="font-medium">
                      {Math.round(rerankingImpact.without_reranking.satisfaction_rate * 100)}%
                    </span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-gray-600">Avg Time:</span>
                    <span className="font-medium">
                      {Math.round(rerankingImpact.without_reranking.avg_search_time)}ms
                    </span>
                  </p>
                </div>
              </div>
              
              {/* Impact summary */}
              <div className="md:col-span-2 bg-blue-50 p-3 rounded-lg">
                <h4 className="text-sm font-medium text-blue-700 mb-2">Impact Summary</h4>
                {rerankingImpact.with_reranking.satisfaction_rate > 0 && 
                 rerankingImpact.without_reranking.satisfaction_rate > 0 && (
                  <p className="text-sm">
                    Reranking 
                    {rerankingImpact.with_reranking.satisfaction_rate > rerankingImpact.without_reranking.satisfaction_rate
                      ? <span className="text-green-600 font-medium"> improves </span>
                      : <span className="text-red-600 font-medium"> reduces </span>
                    }
                    satisfaction by 
                    <span className="font-medium"> {Math.abs(Math.round((
                      rerankingImpact.with_reranking.satisfaction_rate - 
                      rerankingImpact.without_reranking.satisfaction_rate
                    ) * 100))}% </span>
                    but adds an average of 
                    <span className="font-medium"> {Math.round(
                      rerankingImpact.with_reranking.avg_reranking_time
                    )}ms </span>
                    to search time.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* Common search issues */}
        {searchIssues && searchIssues.search_issues && (
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Common Search Issues</h3>
            <div className="space-y-3">
              {searchIssues.search_issues.map((issue, i) => (
                <div key={i} className="flex items-center">
                  <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full" 
                      style={{ 
                        width: `${(issue.count / (searchIssues.search_issues[0]?.count || 1)) * 100}%` 
                      }}
                    />
                  </div>
                  <div className="flex justify-between w-full">
                    <span className="text-sm text-gray-700">{issue.name}</span>
                    <span className="text-sm text-gray-500">{issue.count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };
  
  const renderDocTypesTab = () => {
    if (!docTypeMetrics) {
      return (
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <p className="text-gray-500">No document type metrics available yet.</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {Object.entries(docTypeMetrics).map(([docType, metrics]) => (
          <div key={docType} className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-3 capitalize">{docType} Documents</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Searches</p>
                <p className="text-2xl font-bold">{metrics.search_count}</p>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Feedback Rate</p>
                <p className="text-2xl font-bold">
                  {Math.round((metrics.feedback_count / metrics.search_count) * 100)}%
                </p>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Satisfaction</p>
                <p className="text-2xl font-bold">
                  {Math.round(metrics.satisfaction_rate * 100)}%
                </p>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Avg Search Time</p>
                <p className="text-2xl font-bold">
                  {metrics.avg_search_time ? `${Math.round(metrics.avg_search_time)}ms` : 'N/A'}
                </p>
              </div>
            </div>
            
            {/* Quality ratings by document type */}
            {metrics.rating_metrics && (
              <div className="border-t border-gray-200 pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Quality Ratings</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(metrics.rating_metrics).map(([key, value]) => (
                    value && (
                      <div key={key} className="bg-gray-50 p-3 rounded-lg">
                        <h5 className="text-xs text-gray-600 capitalize mb-1">
                          {key.replace('_', ' ')}
                        </h5>
                        <div className="flex items-center">
                          <div className="flex text-yellow-400 mr-2">
                            {Array.from({ length: 5 }).map((_, i) => (
                              <span key={i} className="text-base">
                                {i < Math.round(value) ? '★' : '☆'}
                              </span>
                            ))}
                          </div>
                          <span className="text-sm text-gray-700">
                            ({value.toFixed(1)})
                          </span>
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };
  
  const renderRankingProfilesTab = () => {
    if (!profileMetrics) {
      return (
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <p className="text-gray-500">No ranking profile metrics available yet.</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {Object.entries(profileMetrics).map(([profileId, metrics]) => (
          <div key={profileId} className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-3">{metrics.profile_name}</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Searches</p>
                <p className="text-2xl font-bold">{metrics.search_count}</p>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Feedback Rate</p>
                <p className="text-2xl font-bold">
                  {Math.round((metrics.feedback_count / metrics.search_count) * 100)}%
                </p>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Satisfaction</p>
                <p className="text-2xl font-bold">
                  {Math.round(metrics.satisfaction_rate * 100)}%
                </p>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Avg Search Time</p>
                <p className="text-2xl font-bold">
                  {metrics.avg_search_time ? `${Math.round(metrics.avg_search_time)}ms` : 'N/A'}
                </p>
              </div>
            </div>
            
            {/* Quality ratings by ranking profile */}
            {metrics.rating_metrics && (
              <div className="border-t border-gray-200 pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Quality Ratings</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(metrics.rating_metrics).map(([key, value]) => (
                    value && (
                      <div key={key} className="bg-gray-50 p-3 rounded-lg">
                        <h5 className="text-xs text-gray-600 capitalize mb-1">
                          {key.replace('_', ' ')}
                        </h5>
                        <div className="flex items-center">
                          <div className="flex text-yellow-400 mr-2">
                            {Array.from({ length: 5 }).map((_, i) => (
                              <span key={i} className="text-base">
                                {i < Math.round(value) ? '★' : '☆'}
                              </span>
                            ))}
                          </div>
                          <span className="text-sm text-gray-700">
                            ({value.toFixed(1)})
                          </span>
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };
  
  const renderPerformanceTab = () => {
    if (!performanceOverTime || !performanceOverTime.length) {
      return (
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <p className="text-gray-500">No performance data available yet.</p>
        </div>
      );
    }
    
    // Time controls
    const renderTimeControls = () => (
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <span className="text-sm text-gray-600">Time Range:</span>
        <div className="flex">
          <button
            onClick={() => handleTimeRangeChange(7, 'day')}
            className={`px-3 py-1 text-sm rounded-l-md ${
              timeRange === 7 ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            7d
          </button>
          <button
            onClick={() => handleTimeRangeChange(30, 'day')}
            className={`px-3 py-1 text-sm ${
              timeRange === 30 && timeInterval === 'day' ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            30d
          </button>
          <button
            onClick={() => handleTimeRangeChange(90, 'week')}
            className={`px-3 py-1 text-sm rounded-r-md ${
              timeRange === 90 ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            90d
          </button>
        </div>
        
        <span className="text-sm text-gray-600 ml-4">Group By:</span>
        <div className="flex">
          <button
            onClick={() => handleTimeRangeChange(timeRange, 'day')}
            className={`px-3 py-1 text-sm rounded-l-md ${
              timeInterval === 'day' ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Day
          </button>
          <button
            onClick={() => handleTimeRangeChange(timeRange, 'week')}
            className={`px-3 py-1 text-sm ${
              timeInterval === 'week' ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Week
          </button>
          <button
            onClick={() => handleTimeRangeChange(timeRange, 'month')}
            className={`px-3 py-1 text-sm rounded-r-md ${
              timeInterval === 'month' ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Month
          </button>
        </div>
      </div>
    );
    
    // Render the performance over time chart
    return (
      <div className="space-y-6">
        {renderTimeControls()}
        
        {/* Search counts and feedback rates over time */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Search Volume & Feedback</h3>
          <div className="h-64">
            {performanceOverTime.map((point, i) => {
              const date = new Date(point.interval).toLocaleDateString();
              const maxCount = Math.max(...performanceOverTime.map(p => p.count));
              const searchHeight = (point.count / maxCount) * 100;
              const feedbackHeight = (point.feedback_count / maxCount) * 100;
              
              return (
                <div key={i} className="inline-block mr-2 align-bottom h-48">
                  <div className="flex flex-col items-center">
                    <div className="h-48 flex items-end">
                      <div 
                        className="w-8 bg-blue-500 mr-1 rounded-t-sm" 
                        style={{ height: `${searchHeight}%` }}
                        title={`Searches: ${point.count}`}
                      />
                      <div 
                        className="w-8 bg-green-500 rounded-t-sm" 
                        style={{ height: `${feedbackHeight}%` }}
                        title={`Feedback: ${point.feedback_count}`}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-1 w-16 text-center">
                      {date}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-center mt-2">
            <div className="flex items-center mr-4">
              <div className="w-3 h-3 bg-blue-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">Searches</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">Feedback</span>
            </div>
          </div>
        </div>
        
        {/* Search times over time */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Search Performance Times</h3>
          <div className="h-64">
            {performanceOverTime.map((point, i) => {
              const date = new Date(point.interval).toLocaleDateString();
              const maxTime = Math.max(
                ...performanceOverTime.map(p => 
                  Math.max(
                    p.avg_search_time || 0, 
                    p.avg_reranking_time || 0, 
                    p.avg_answer_time || 0
                  )
                )
              );
              
              const searchTimeHeight = ((point.avg_search_time || 0) / maxTime) * 100;
              const rerankingTimeHeight = ((point.avg_reranking_time || 0) / maxTime) * 100;
              const answerTimeHeight = ((point.avg_answer_time || 0) / maxTime) * 100;
              
              return (
                <div key={i} className="inline-block mr-2 align-bottom h-48">
                  <div className="flex flex-col items-center">
                    <div className="h-48 flex items-end">
                      <div 
                        className="w-4 bg-blue-500 mr-1 rounded-t-sm" 
                        style={{ height: `${searchTimeHeight}%` }}
                        title={`Search: ${Math.round(point.avg_search_time || 0)}ms`}
                      />
                      <div 
                        className="w-4 bg-purple-500 mr-1 rounded-t-sm" 
                        style={{ height: `${rerankingTimeHeight}%` }}
                        title={`Reranking: ${Math.round(point.avg_reranking_time || 0)}ms`}
                      />
                      <div 
                        className="w-4 bg-yellow-500 rounded-t-sm" 
                        style={{ height: `${answerTimeHeight}%` }}
                        title={`Answer: ${Math.round(point.avg_answer_time || 0)}ms`}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-1 w-16 text-center">
                      {date}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-center mt-2">
            <div className="flex items-center mr-4">
              <div className="w-3 h-3 bg-blue-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">Search Time</span>
            </div>
            <div className="flex items-center mr-4">
              <div className="w-3 h-3 bg-purple-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">Reranking Time</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">Answer Time</span>
            </div>
          </div>
        </div>
        
        {/* Satisfaction rate over time */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Search Satisfaction Rate</h3>
          <div className="h-64">
            {performanceOverTime.map((point, i) => {
              const date = new Date(point.interval).toLocaleDateString();
              const satisfactionHeight = (point.satisfaction_rate || 0) * 100;
              
              return (
                <div key={i} className="inline-block mr-2 align-bottom h-48">
                  <div className="flex flex-col items-center">
                    <div className="h-48 flex items-end">
                      <div 
                        className="w-8 rounded-t-sm"
                        style={{ 
                          height: `${satisfactionHeight}%`,
                          backgroundColor: satisfactionHeight > 75 
                            ? '#22c55e' // green-500
                            : satisfactionHeight > 50 
                              ? '#eab308' // yellow-500
                              : '#ef4444' // red-500
                        }}
                        title={`Satisfaction: ${Math.round(satisfactionHeight)}%`}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-1 w-16 text-center">
                      {date}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-center mt-2">
            <div className="flex items-center mr-4">
              <div className="w-3 h-3 bg-green-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">High (&gt;75%)</span>
            </div>
            <div className="flex items-center mr-4">
              <div className="w-3 h-3 bg-yellow-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">Medium (50-75%)</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 mr-1 rounded-sm"></div>
              <span className="text-xs text-gray-600">Low ({"<"}50%)</span>
            </div>
          </div>
        </div>
      </div>
    );
  };
  
  const renderIssuesTab = () => {
    if (!searchIssues) {
      return (
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <p className="text-gray-500">No search issues data available yet.</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* All issues */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Top Search Issues</h3>
          {searchIssues.all_issues && searchIssues.all_issues.length > 0 ? (
            <div className="space-y-3">
              {searchIssues.all_issues.map((issue, i) => (
                <div key={i} className="flex items-center">
                  <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full" 
                      style={{ width: `${(issue.count / searchIssues.all_issues[0].count) * 100}%` }}
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
        
        {/* Search-specific issues */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Search issues */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Search Issues</h3>
            {searchIssues.search_issues && searchIssues.search_issues.length > 0 ? (
              <div className="space-y-2">
                {searchIssues.search_issues.map((issue, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-sm text-gray-700">{issue.name}</span>
                    <span className="text-sm text-gray-500">{issue.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No search issues reported</p>
            )}
          </div>
          
          {/* Ranking issues */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Ranking Issues</h3>
            {searchIssues.ranking_issues && searchIssues.ranking_issues.length > 0 ? (
              <div className="space-y-2">
                {searchIssues.ranking_issues.map((issue, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-sm text-gray-700">{issue.name}</span>
                    <span className="text-sm text-gray-500">{issue.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No ranking issues reported</p>
            )}
          </div>
          
          {/* Relevance issues */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Relevance Issues</h3>
            {searchIssues.relevance_issues && searchIssues.relevance_issues.length > 0 ? (
              <div className="space-y-2">
                {searchIssues.relevance_issues.map((issue, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-sm text-gray-700">{issue.name}</span>
                    <span className="text-sm text-gray-500">{issue.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No relevance issues reported</p>
            )}
          </div>
          
          {/* Other issues */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Other Issues</h3>
            {searchIssues.other_issues && searchIssues.other_issues.length > 0 ? (
              <div className="space-y-2">
                {searchIssues.other_issues.map((issue, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-sm text-gray-700">{issue.name}</span>
                    <span className="text-sm text-gray-500">{issue.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No other issues reported</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-pulse text-gray-600">Loading search quality data...</div>
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
      <h2 className="text-2xl font-bold mb-6">Search Quality Dashboard</h2>
      
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
              onClick={() => setActiveTab('docTypes')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'docTypes'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Document Types
            </button>
            <button
              onClick={() => setActiveTab('rankingProfiles')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'rankingProfiles'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Ranking Profiles
            </button>
            <button
              onClick={() => setActiveTab('performance')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'performance'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Performance
            </button>
            <button
              onClick={() => setActiveTab('issues')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'issues'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Issues
            </button>
          </nav>
        </div>
      </div>
      
      <div>
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'docTypes' && renderDocTypesTab()}
        {activeTab === 'rankingProfiles' && renderRankingProfilesTab()}
        {activeTab === 'performance' && renderPerformanceTab()}
        {activeTab === 'issues' && renderIssuesTab()}
      </div>
    </div>
  );
};

export default SearchQualityDashboard;