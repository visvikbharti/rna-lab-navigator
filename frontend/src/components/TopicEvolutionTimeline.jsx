import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './enhanced/Card';
import { Button } from './enhanced/Button';
import { getTopicEvolution } from '../api/intelligence';
import { TrendingUp, TrendingDown, Activity, Calendar } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const TopicEvolutionTimeline = ({ specificTopic = '' }) => {
  const [loading, setLoading] = useState(false);
  const [evolutionData, setEvolutionData] = useState(null);
  const [timeWindow, setTimeWindow] = useState(365);
  const [selectedPeriod, setSelectedPeriod] = useState(null);

  useEffect(() => {
    fetchEvolutionData();
  }, [timeWindow, specificTopic]);

  const fetchEvolutionData = async () => {
    setLoading(true);
    try {
      const params = { days: timeWindow };
      if (specificTopic) {
        params.topic = specificTopic;
      }
      
      const data = await getTopicEvolution(params);
      setEvolutionData(data);
    } catch (error) {
      console.error('Error fetching evolution data:', error);
    }
    setLoading(false);
  };

  const prepareChartData = () => {
    if (!evolutionData?.chart_data) return null;

    const { labels, datasets } = evolutionData.chart_data;
    
    // Convert datasets object to array format for Chart.js
    const chartDatasets = Object.entries(datasets).slice(0, 10).map(([topic, data], index) => {
      const colors = [
        'rgb(59, 130, 246)', // blue
        'rgb(239, 68, 68)',  // red
        'rgb(34, 197, 94)',  // green
        'rgb(251, 146, 60)', // orange
        'rgb(168, 85, 247)', // purple
        'rgb(236, 72, 153)', // pink
        'rgb(20, 184, 166)', // teal
        'rgb(251, 191, 36)', // amber
        'rgb(99, 102, 241)', // indigo
        'rgb(244, 63, 94)'   // rose
      ];

      return {
        label: topic,
        data: data,
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length] + '20',
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
      };
    });

    return {
      labels,
      datasets: chartDatasets
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Research Topic Evolution Over Time'
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Topic Score'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Time Period'
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  const renderTrendingTopics = (topics, direction) => {
    const icon = direction === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />;
    const colorClass = direction === 'up' ? 'text-green-600' : 'text-red-600';

    return (
      <div className="space-y-2">
        {topics.slice(0, 5).map((topic, idx) => (
          <div key={idx} className={`flex items-center justify-between ${colorClass}`}>
            <div className="flex items-center gap-2">
              {icon}
              <span className="text-sm font-medium">{topic.topic}</span>
            </div>
            <span className="text-xs">
              {direction === 'up' ? '+' : ''}{(topic.growth_rate * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    );
  };

  const chartData = prepareChartData();

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-6 h-6" />
          Topic Evolution Timeline
        </CardTitle>
        <div className="flex gap-2 mt-4">
          <select
            value={timeWindow}
            onChange={(e) => setTimeWindow(Number(e.target.value))}
            className="px-3 py-2 border rounded-md"
          >
            <option value={90}>Last 3 months</option>
            <option value={180}>Last 6 months</option>
            <option value={365}>Last year</option>
            <option value={730}>Last 2 years</option>
          </select>
          <Button onClick={fetchEvolutionData} disabled={loading}>
            <Calendar className="w-4 h-4 mr-2" />
            Update
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : evolutionData ? (
          <div className="space-y-6">
            {/* Chart */}
            {chartData && (
              <div className="h-96">
                <Line data={chartData} options={chartOptions} />
              </div>
            )}

            {/* Trending Topics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Trending Up */}
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold mb-3 text-green-800">Trending Up</h4>
                {evolutionData.trending_up?.length > 0 ? (
                  renderTrendingTopics(evolutionData.trending_up, 'up')
                ) : (
                  <p className="text-sm text-gray-500">No upward trends detected</p>
                )}
              </div>

              {/* Stable Topics */}
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold mb-3 text-blue-800">Stable Topics</h4>
                {evolutionData.stable_topics?.length > 0 ? (
                  <div className="space-y-2">
                    {evolutionData.stable_topics.slice(0, 5).map((topic, idx) => (
                      <div key={idx} className="flex items-center justify-between text-blue-600">
                        <span className="text-sm font-medium">{topic.topic}</span>
                        <span className="text-xs">
                          {(topic.consistency * 100).toFixed(0)}% consistent
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No stable topics found</p>
                )}
              </div>

              {/* Trending Down */}
              <div className="p-4 bg-red-50 rounded-lg">
                <h4 className="font-semibold mb-3 text-red-800">Trending Down</h4>
                {evolutionData.trending_down?.length > 0 ? (
                  renderTrendingTopics(evolutionData.trending_down, 'down')
                ) : (
                  <p className="text-sm text-gray-500">No downward trends detected</p>
                )}
              </div>
            </div>

            {/* Topic Transitions */}
            {evolutionData.topic_transitions?.length > 0 && (
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold mb-3 text-purple-800">Topic Transitions</h4>
                <div className="space-y-2">
                  {evolutionData.topic_transitions.slice(0, 5).map((transition, idx) => (
                    <div key={idx} className="text-sm">
                      <span className="font-medium text-purple-600">{transition.from}</span>
                      <span className="mx-2">→</span>
                      <span className="font-medium text-purple-600">{transition.to}</span>
                      <span className="text-xs text-gray-500 ml-2">({transition.period})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Future Predictions */}
            {evolutionData.predicted_future_topics?.length > 0 && (
              <div className="p-4 bg-amber-50 rounded-lg">
                <h4 className="font-semibold mb-3 text-amber-800">Predicted Future Topics</h4>
                <div className="space-y-2">
                  {evolutionData.predicted_future_topics.slice(0, 5).map((prediction, idx) => (
                    <div key={idx} className="border-l-4 border-amber-400 pl-3 py-1">
                      <div className="font-medium text-sm text-amber-700">{prediction.topic}</div>
                      <div className="text-xs text-gray-600">
                        Confidence: {(prediction.confidence * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{prediction.suggested_focus}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timeline Details */}
            {evolutionData.timeline?.length > 0 && (
              <div className="mt-6">
                <h4 className="font-semibold mb-3">Period Details</h4>
                <div className="space-y-2">
                  {evolutionData.timeline.map((period, idx) => (
                    <div
                      key={idx}
                      className="p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => setSelectedPeriod(period)}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{period.period}</span>
                        <span className="text-sm text-gray-500">
                          {period.document_count} documents
                        </span>
                      </div>
                      {period.emerging_topics?.length > 0 && (
                        <div className="mt-1 flex gap-2 flex-wrap">
                          {period.emerging_topics.map((topic, tidx) => (
                            <span key={tidx} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                              New: {topic}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-4" />
            <p>Select a time window to view topic evolution</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TopicEvolutionTimeline;