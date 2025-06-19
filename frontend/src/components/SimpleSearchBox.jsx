import { useState } from 'react';
import { motion } from 'framer-motion';

const SimpleSearchBox = ({ onSearch }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const exampleQueries = [
    { category: "Thesis findings", queries: [
      "What DNA repair mechanisms are studied in Rhythm Phutela thesis regarding Cas9 cleavage?",
      "How does NHEJ differ from HDR in Cas9-mediated DNA repair according to Rhythm's thesis?",
      "What is the title and focus of Rhythm Phutela's PhD thesis?"
    ]},
    { category: "CRISPR diagnostics", queries: [
      "What is the RAPID FnCas9 system developed by Kumar for COVID detection?",
      "Explain the FnCas9-based SNP detection method from Kumar's 2022 paper",
      "How does the FELUDA diagnostic platform work?"
    ]},
    { category: "Lab protocols", queries: [
      "What is the protocol for RNA extraction using Trizol?",
      "How do I perform qPCR according to the lab manual?",
      "What are the steps for Western blot in the lab protocol?"
    ]}
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          doc_type: 'all'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        onSearch(data);
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-5xl mx-auto px-4"
    >
      {/* Header Section */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-3">
          RNA Lab Navigator
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          AI-powered research assistant for Dr. Debojyoti Chakraborty's RNA Biology Lab
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What DNA repair mechanisms are studied in Rhythm Phutela's thesis?"
            className="w-full px-6 py-4 pr-24 text-lg rounded-xl border-2 border-gray-300 dark:border-gray-600 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                       placeholder-gray-500 dark:placeholder-gray-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 px-6 py-2.5 
                       bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all duration-200"
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching...
              </span>
            ) : 'Search'}
          </button>
        </div>
      </form>

      {/* Example Queries Section */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 mb-6">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4">
          Try these example queries:
        </h3>
        
        <div className="flex gap-2 mb-4 flex-wrap">
          {exampleQueries.map((category, idx) => (
            <button
              key={idx}
              className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              onClick={() => {}}
            >
              {category.category}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          {exampleQueries.map((category, idx) => (
            <div key={idx} className="space-y-2">
              {category.queries.map((q, qIdx) => (
                <button
                  key={qIdx}
                  onClick={() => handleExampleClick(q)}
                  className="block w-full text-left text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Stats Section */}
      <div className="text-center text-xs text-gray-500 dark:text-gray-400">
        <p>Searches across <span className="font-semibold">31 documents</span> • 
           <span className="font-semibold"> 1 thesis</span> • 
           <span className="font-semibold"> 18 papers</span> • 
           <span className="font-semibold"> 9 protocols</span>
        </p>
      </div>
    </motion.div>
  );
};

export default SimpleSearchBox;