import React, { useState, useEffect } from 'react';
import { Play, Pause, X, CheckCircle, AlertCircle, FileText, Clock, Users } from 'lucide-react';
import { getDocuments, getProcessingStatus } from '../api/ingestion';
import { useProcessingWebSocket } from '../hooks/useWebSocket';

const BatchProcessingManager = () => {
  const [batches, setBatches] = useState([]);
  const [activeBatch, setActiveBatch] = useState(null);
  const [statistics, setStatistics] = useState({
    totalProcessed: 0,
    successRate: 0,
    avgProcessingTime: 0,
    activeJobs: 0
  });

  // WebSocket for active batch
  const { connected, lastMessage } = useProcessingWebSocket(activeBatch?.id);

  useEffect(() => {
    loadBatches();
    const interval = setInterval(loadBatches, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (lastMessage && activeBatch) {
      handleBatchUpdate(activeBatch.id, lastMessage);
    }
  }, [lastMessage, activeBatch]);

  const loadBatches = async () => {
    // Load batch processing history from localStorage or API
    const storedBatches = JSON.parse(localStorage.getItem('processingBatches') || '[]');
    setBatches(storedBatches);
    
    // Calculate statistics
    const stats = calculateStatistics(storedBatches);
    setStatistics(stats);
  };

  const calculateStatistics = (batchList) => {
    const completed = batchList.filter(b => b.status === 'completed');
    const successful = completed.filter(b => b.failedCount === 0);
    const totalTime = completed.reduce((sum, b) => sum + (b.processingTime || 0), 0);
    const active = batchList.filter(b => b.status === 'processing').length;

    return {
      totalProcessed: completed.length,
      successRate: completed.length > 0 ? (successful.length / completed.length * 100).toFixed(1) : 0,
      avgProcessingTime: completed.length > 0 ? (totalTime / completed.length / 60).toFixed(1) : 0,
      activeJobs: active
    };
  };

  const handleBatchUpdate = (batchId, data) => {
    setBatches(prev => prev.map(batch => {
      if (batch.id === batchId) {
        if (data.type === 'batch_completed') {
          return {
            ...batch,
            status: 'completed',
            results: data.data,
            completedAt: new Date().toISOString(),
            processingTime: Date.now() - new Date(batch.startedAt).getTime()
          };
        } else if (data.type === 'progress') {
          return {
            ...batch,
            progress: data.data
          };
        }
      }
      return batch;
    }));
  };

  const cancelBatch = (batchId) => {
    // Send cancel request via WebSocket
    if (connected && activeBatch?.id === batchId) {
      // WebSocket send cancel command
    }
    
    setBatches(prev => prev.map(batch => 
      batch.id === batchId 
        ? { ...batch, status: 'cancelled' }
        : batch
    ));
  };

  const retryBatch = (batch) => {
    // Implement retry logic
    console.log('Retrying batch:', batch.id);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Statistics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<FileText className="h-6 w-6 text-blue-600" />}
          title="Total Processed"
          value={statistics.totalProcessed}
          subtitle="Batches completed"
        />
        <StatCard
          icon={<CheckCircle className="h-6 w-6 text-green-600" />}
          title="Success Rate"
          value={`${statistics.successRate}%`}
          subtitle="Without errors"
        />
        <StatCard
          icon={<Clock className="h-6 w-6 text-purple-600" />}
          title="Avg. Time"
          value={`${statistics.avgProcessingTime}m`}
          subtitle="Per batch"
        />
        <StatCard
          icon={<Users className="h-6 w-6 text-orange-600" />}
          title="Active Jobs"
          value={statistics.activeJobs}
          subtitle="Currently processing"
        />
      </div>

      {/* Batch List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Processing History</h2>
        </div>
        
        <div className="divide-y divide-gray-200">
          {batches.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-500">
              No batch processing history
            </div>
          ) : (
            batches.map((batch) => (
              <BatchItem
                key={batch.id}
                batch={batch}
                isActive={activeBatch?.id === batch.id}
                onSelect={() => setActiveBatch(batch)}
                onCancel={() => cancelBatch(batch.id)}
                onRetry={() => retryBatch(batch)}
                getStatusIcon={getStatusIcon}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icon, title, value, subtitle }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{subtitle}</p>
      </div>
      <div className="p-3 bg-gray-50 rounded-full">
        {icon}
      </div>
    </div>
  </div>
);

const BatchItem = ({ batch, isActive, onSelect, onCancel, onRetry, getStatusIcon }) => {
  const getProgressPercentage = () => {
    if (!batch.progress) return 0;
    const { processed_chunks, total_chunks } = batch.progress;
    return total_chunks > 0 ? (processed_chunks / total_chunks * 100).toFixed(1) : 0;
  };

  return (
    <div 
      className={`px-6 py-4 hover:bg-gray-50 cursor-pointer ${
        isActive ? 'bg-blue-50' : ''
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {getStatusIcon(batch.status)}
          <div>
            <p className="text-sm font-medium text-gray-900">
              Batch {batch.id.substring(0, 8)}
            </p>
            <p className="text-sm text-gray-500">
              {batch.fileCount} files • Started {new Date(batch.startedAt).toLocaleString()}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {batch.status === 'processing' && (
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${getProgressPercentage()}%` }}
                />
              </div>
              <span className="text-sm text-gray-600">
                {getProgressPercentage()}%
              </span>
            </div>
          )}
          
          {batch.status === 'completed' && batch.results && (
            <div className="text-sm text-gray-600">
              {batch.results.successful}/{batch.results.total} succeeded
            </div>
          )}
          
          <div className="flex space-x-2">
            {batch.status === 'processing' && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCancel();
                }}
                className="p-1 text-red-600 hover:bg-red-50 rounded"
                title="Cancel batch"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            
            {(batch.status === 'failed' || batch.status === 'cancelled') && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRetry();
                }}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Expanded Details */}
      {isActive && batch.progress && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Current Stage:</p>
              <p className="font-medium">{batch.progress.current_stage}</p>
            </div>
            <div>
              <p className="text-gray-600">Processing Time:</p>
              <p className="font-medium">{Math.floor(batch.progress.elapsed_time / 60)}m {Math.floor(batch.progress.elapsed_time % 60)}s</p>
            </div>
            {batch.progress.errors.length > 0 && (
              <div className="col-span-2">
                <p className="text-gray-600 mb-1">Errors:</p>
                <ul className="list-disc list-inside text-red-600">
                  {batch.progress.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchProcessingManager;