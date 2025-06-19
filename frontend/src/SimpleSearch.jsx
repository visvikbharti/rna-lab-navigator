import { useState } from 'react';
import SimpleSearchBox from './components/SimpleSearchBox';
import AnswerCard from './components/AnswerCard';
import { GlassCard } from './components/enhanced';

function SimpleSearch() {
  const [searchResult, setSearchResult] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (result) => {
    // Transform the result to match AnswerCard format
    const formattedResult = {
      answer: result.answer,
      sources: result.sources || [],
      confidence_score: result.confidence_score || 0,
      search_results: result.search_results || [],
      processing_time: result.processing_time || 0
    };
    setSearchResult(formattedResult);
    setIsSearching(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            RNA Lab Navigator - Simple Search
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Ask questions about your lab's research and get instant, cited answers
          </p>
        </div>
      </div>

      {/* Search Section */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <SimpleSearchBox onSearch={handleSearch} />

        {/* Results Section */}
        {searchResult && (
          <div className="mt-8">
            <AnswerCard response={searchResult} />
          </div>
        )}
      </div>
    </div>
  );
}

export default SimpleSearch;