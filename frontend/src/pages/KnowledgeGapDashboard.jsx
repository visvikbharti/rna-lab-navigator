import React, { useState } from 'react';
import { motion } from 'framer-motion';
import KnowledgeGapHeatmap from '../components/KnowledgeGapHeatmap';
import TopicEvolutionTimeline from '../components/TopicEvolutionTimeline';
import GapExplorer from '../components/GapExplorer';
import { GradientText } from '../components/enhanced';
import { 
  ChartBarIcon, 
  LightBulbIcon, 
  TrendingUpIcon,
  BeakerIcon,
  DocumentMagnifyingGlassIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';

const KnowledgeGapDashboard = () => {
  const [activeTab, setActiveTab] = useState('explorer');
  const [selectedDomain, setSelectedDomain] = useState('');

  const tabs = [
    { id: 'explorer', name: 'Gap Explorer', icon: DocumentMagnifyingGlassIcon },
    { id: 'heatmap', name: 'Coverage Heatmap', icon: ChartBarIcon },
    { id: 'evolution', name: 'Topic Evolution', icon: TrendingUpIcon },
  ];

  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5 }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <motion.div 
        className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <GradientText className="text-3xl font-bold" gradient="ocean">
                Knowledge Gap Intelligence
              </GradientText>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Discover unexplored research areas and opportunities in your field
              </p>
            </div>
            <div className="flex items-center gap-4">
              <BeakerIcon className="w-10 h-10 text-blue-500" />
              <AcademicCapIcon className="w-10 h-10 text-purple-500" />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats Overview */}
      <motion.div 
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"
        {...fadeIn}
        transition={{ delay: 0.2 }}
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <motion.div 
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Gaps Identified</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">247</p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                <LightBulbIcon className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Research Opportunities</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">89</p>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full">
                <TrendingUpIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Coverage Score</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">73%</p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                <ChartBarIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Emerging Topics</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">15</p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                <BeakerIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div 
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
        {...fadeIn}
        transition={{ delay: 0.3 }}
      >
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                  }
                `}
              >
                <tab.icon className="w-5 h-5" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </motion.div>

      {/* Tab Content */}
      <motion.div 
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"
        {...fadeIn}
        transition={{ delay: 0.4 }}
      >
        {activeTab === 'explorer' && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <GapExplorer 
              onSelectGap={(gap) => {
                console.log('Selected gap:', gap);
                // Could navigate to detailed view or update other components
              }}
            />
          </motion.div>
        )}

        {activeTab === 'heatmap' && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <KnowledgeGapHeatmap 
              initialDomain={selectedDomain}
            />
          </motion.div>
        )}

        {activeTab === 'evolution' && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <TopicEvolutionTimeline 
              specificTopic={selectedDomain}
            />
          </motion.div>
        )}
      </motion.div>

      {/* Quick Actions */}
      <motion.div 
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12"
        {...fadeIn}
        transition={{ delay: 0.5 }}
      >
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-xl p-8 text-white">
          <h3 className="text-2xl font-bold mb-4">Ready to Fill Research Gaps?</h3>
          <p className="text-lg mb-6 opacity-90">
            Our AI has identified key areas where your research can make the biggest impact.
          </p>
          <div className="flex flex-wrap gap-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Download Gap Report
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-blue-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-800 transition-colors"
            >
              Schedule Research Planning Session
            </motion.button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default KnowledgeGapDashboard;