import React, { useState } from 'react';
import { 
  BeakerIcon, 
  LightBulbIcon, 
  DocumentDuplicateIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import api from '../api/client';

const MultiAgentAnalysis = () => {
  const [papers, setPapers] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('patterns');
  const [error, setError] = useState(null);

  // Sample papers for demo
  const addSamplePapers = () => {
    setPapers([
      {
        id: "paper1",
        title: "CRISPR-Cas9 efficiency in primary T cells depends on nucleofection parameters",
        authors: "Smith et al.",
        year: "2023",
        abstract: "We found that nucleofection program DN-100 achieves 95% editing efficiency in primary human T cells with minimal toxicity.",
        selected: true
      },
      {
        id: "paper2",
        title: "Optimizing CRISPR delivery in hard-to-transfect immune cells",
        authors: "Johnson et al.",
        year: "2023",
        abstract: "Our study shows that electroporation program T-023 is superior for T cell editing, achieving only 60% efficiency but with better cell viability.",
        selected: true
      },
      {
        id: "paper3",
        title: "Novel RNP formulations enhance CRISPR editing in lymphocytes",
        authors: "Chen et al.",
        year: "2024",
        abstract: "Adding cell-penetrating peptides to RNP complexes increased editing to 98% in T cells using standard nucleofection.",
        selected: true
      }
    ]);
  };

  const runCrossPaperAnalysis = async () => {
    const selectedPapers = papers.filter(p => p.selected);
    if (selectedPapers.length < 2) {
      setError("Please select at least 2 papers for analysis");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/agents/cross-paper-analysis/', {
        papers: selectedPapers,
        area: "CRISPR optimization"
      });

      setAnalysisResults(response.data.report);
    } catch (err) {
      setError(err.response?.data?.error || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const togglePaperSelection = (paperId) => {
    setPapers(papers.map(p => 
      p.id === paperId ? { ...p, selected: !p.selected } : p
    ));
  };

  const renderPatterns = () => {
    if (!analysisResults?.key_patterns) return null;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <SparklesIcon className="h-5 w-5 mr-2 text-blue-500" />
          Key Patterns Discovered
        </h3>
        {analysisResults.key_patterns.map((pattern, idx) => (
          <div key={idx} className="bg-blue-50 p-4 rounded-lg">
            <p className="text-gray-800">
              {pattern.pattern || pattern}
            </p>
            {pattern.evidence && (
              <p className="text-sm text-gray-600 mt-2">
                Evidence from: {pattern.evidence.join(', ')}
              </p>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderContradictions = () => {
    if (!analysisResults?.major_contradictions) return null;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <ExclamationTriangleIcon className="h-5 w-5 mr-2 text-red-500" />
          Major Contradictions Found
        </h3>
        {analysisResults.major_contradictions.map((contradiction, idx) => (
          <div key={idx} className="bg-red-50 p-4 rounded-lg">
            <p className="text-gray-800 font-medium">
              {contradiction.explanation || contradiction}
            </p>
            {contradiction.type && (
              <div className="mt-2 flex items-center space-x-4 text-sm">
                <span className="text-gray-600">Type: {contradiction.type}</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  contradiction.severity === 'high' ? 'bg-red-200 text-red-800' :
                  contradiction.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                  'bg-green-200 text-green-800'
                }`}>
                  {contradiction.severity || 'medium'} severity
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderHypotheses = () => {
    if (!analysisResults?.novel_hypotheses) return null;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-500" />
          Novel Hypotheses Generated
        </h3>
        {analysisResults.novel_hypotheses.map((hypothesis, idx) => (
          <div key={idx} className="bg-yellow-50 p-4 rounded-lg">
            <p className="text-gray-800">
              {hypothesis.hypothesis || hypothesis}
            </p>
            {hypothesis.type && (
              <p className="text-sm text-gray-600 mt-2">
                Type: {hypothesis.type}
              </p>
            )}
            <button 
              onClick={() => window.location.href = '#protocol-designer'}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Design protocol for this hypothesis →
            </button>
          </div>
        ))}
      </div>
    );
  };

  const renderGaps = () => {
    if (!analysisResults?.research_gaps) return null;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <DocumentDuplicateIcon className="h-5 w-5 mr-2 text-purple-500" />
          Research Gaps Identified
        </h3>
        {analysisResults.research_gaps.map((gap, idx) => (
          <div key={idx} className="bg-purple-50 p-4 rounded-lg">
            <p className="text-gray-800">{gap.gap || gap}</p>
            {gap.opportunity && (
              <p className="text-sm text-gray-600 mt-2">
                Opportunity: {gap.opportunity}
              </p>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderNextSteps = () => {
    if (!analysisResults?.next_steps) return null;

    return (
      <div className="mt-6 bg-green-50 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Recommended Next Steps
        </h3>
        <ol className="space-y-2">
          {analysisResults.next_steps.map((step, idx) => (
            <li key={idx} className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 bg-green-500 text-white rounded-full text-sm flex items-center justify-center mr-3">
                {idx + 1}
              </span>
              <span className="text-gray-700">{step}</span>
            </li>
          ))}
        </ol>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Multi-Agent Research Analysis
          </h2>
          <p className="text-gray-600">
            Our AI research team will analyze papers to find patterns, contradictions, and generate novel hypotheses
          </p>
        </div>

        {/* Paper Selection */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Select Papers for Analysis</h3>
            <button
              onClick={addSamplePapers}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Load sample papers
            </button>
          </div>

          {papers.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <DocumentDuplicateIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">No papers loaded</p>
              <button
                onClick={addSamplePapers}
                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Load Sample Papers
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {papers.map(paper => (
                <div 
                  key={paper.id}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                    paper.selected 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => togglePaperSelection(paper.id)}
                >
                  <div className="flex items-start">
                    <input
                      type="checkbox"
                      checked={paper.selected}
                      onChange={() => {}}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{paper.title}</h4>
                      <p className="text-sm text-gray-600">{paper.authors} • {paper.year}</p>
                      <p className="text-sm text-gray-700 mt-1">{paper.abstract}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Analysis Button */}
        <div className="mb-8">
          <button
            onClick={runCrossPaperAnalysis}
            disabled={loading || papers.filter(p => p.selected).length < 2}
            className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <>
                <ArrowPathIcon className="h-5 w-5 mr-2 animate-spin" />
                Analyzing papers...
              </>
            ) : (
              <>
                <BeakerIcon className="h-5 w-5 mr-2" />
                Run Multi-Agent Analysis
              </>
            )}
          </button>
          {error && (
            <p className="mt-2 text-red-600 text-sm text-center">{error}</p>
          )}
        </div>

        {/* Results */}
        {analysisResults && (
          <div>
            <div className="border-b border-gray-200 mb-6">
              <nav className="-mb-px flex space-x-8">
                {['patterns', 'contradictions', 'hypotheses', 'gaps'].map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </nav>
            </div>

            <div className="space-y-6">
              {activeTab === 'patterns' && renderPatterns()}
              {activeTab === 'contradictions' && renderContradictions()}
              {activeTab === 'hypotheses' && renderHypotheses()}
              {activeTab === 'gaps' && renderGaps()}
            </div>

            {renderNextSteps()}
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiAgentAnalysis;