import React, { useState, useEffect } from 'react';
import { 
  DocumentTextIcon, 
  BellIcon, 
  ClockIcon, 
  SparklesIcon,
  BeakerIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { BellAlertIcon } from '@heroicons/react/24/solid';

const PaperDashboard = () => {
  const [stats, setStats] = useState(null);
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('urgent');
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    fetchDashboard();
    fetchPapers();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await fetch('/api/papers/dashboard/');
      const data = await response.json();
      setStats(data.stats);
      if (data.recent_papers) {
        setPapers(data.recent_papers);
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPapers = async (category = 'urgent') => {
    try {
      const response = await fetch(`/api/papers/list/?category=${category}&limit=20`);
      const data = await response.json();
      setPapers(data.papers || []);
    } catch (error) {
      console.error('Error fetching papers:', error);
    }
  };

  const checkPapersNow = async () => {
    setChecking(true);
    try {
      const response = await fetch('/api/papers/check-now/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hours: 24 })
      });
      const data = await response.json();
      
      if (data.success) {
        alert(`Found ${data.urgent} urgent and ${data.relevant} relevant papers!`);
        fetchDashboard();
        fetchPapers();
      }
    } catch (error) {
      console.error('Error checking papers:', error);
    } finally {
      setChecking(false);
    }
  };

  const getCategoryIcon = (category) => {
    switch(category) {
      case 'urgent':
        return <BellAlertIcon className="w-5 h-5 text-red-500" />;
      case 'relevant':
        return <DocumentTextIcon className="w-5 h-5 text-blue-500" />;
      case 'monitoring':
        return <ClockIcon className="w-5 h-5 text-gray-500" />;
      default:
        return <DocumentTextIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getCategoryBadge = (category) => {
    const styles = {
      urgent: 'bg-red-100 text-red-800 border-red-200',
      relevant: 'bg-blue-100 text-blue-800 border-blue-200',
      monitoring: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[category] || styles.monitoring}`}>
        {category.charAt(0).toUpperCase() + category.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Paper Intelligence Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Stay ahead with the latest research in RNA biology and CRISPR
          </p>
        </div>
        
        <button
          onClick={checkPapersNow}
          disabled={checking}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {checking ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Checking...
            </>
          ) : (
            <>
              <BellIcon className="w-4 h-4 mr-2" />
              Check Papers Now
            </>
          )}
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BellAlertIcon className="h-6 w-6 text-red-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Urgent Papers
                    </dt>
                    <dd className="text-2xl font-semibold text-gray-900">
                      {stats.urgent_papers}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Relevant Papers
                    </dt>
                    <dd className="text-2xl font-semibold text-gray-900">
                      {stats.relevant_papers}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BeakerIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Papers Ingested
                    </dt>
                    <dd className="text-2xl font-semibold text-gray-900">
                      {stats.papers_ingested}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ClockIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Monitored
                    </dt>
                    <dd className="text-2xl font-semibold text-gray-900">
                      {stats.total_monitored}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['urgent', 'relevant', 'monitoring', 'all'].map((category) => (
            <button
              key={category}
              onClick={() => {
                setSelectedCategory(category);
                fetchPapers(category);
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedCategory === category
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Papers List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {papers.length === 0 ? (
            <li className="px-6 py-12 text-center text-gray-500">
              No papers found in this category
            </li>
          ) : (
            papers.map((paper) => (
              <li key={paper.id} className="hover:bg-gray-50">
                <div className="px-6 py-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        {getCategoryIcon(paper.relevance_category)}
                        <h3 className="ml-2 text-lg font-medium text-gray-900">
                          {paper.title}
                        </h3>
                      </div>
                      
                      <p className="mt-1 text-sm text-gray-600">
                        {paper.authors}
                      </p>
                      
                      {paper.smart_summary && (
                        <div className="mt-2 text-sm text-gray-700 bg-blue-50 p-3 rounded">
                          <div className="flex items-start">
                            <SparklesIcon className="w-4 h-4 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                            <div>
                              <p className="font-medium text-blue-900">AI Summary:</p>
                              <p>{paper.smart_summary}</p>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      <div className="mt-3 flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          {getCategoryBadge(paper.relevance_category)}
                          <span className="text-sm text-gray-500">
                            Score: {paper.relevance_score}
                          </span>
                          <span className="text-sm text-gray-500">
                            {new Date(paper.published_date).toLocaleDateString()}
                          </span>
                        </div>
                        
                        <a
                          href={paper.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
                        >
                          Read Paper
                          <ArrowRightIcon className="ml-1 w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
};

export default PaperDashboard;