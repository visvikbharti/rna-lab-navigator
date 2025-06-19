import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './enhanced/Card';
import { Button } from './enhanced/Button';
import { analyzeGaps } from '../api/intelligence';
import { AlertCircle, Info, TrendingUp, Search } from 'lucide-react';

const KnowledgeGapHeatmap = ({ initialDomain = '' }) => {
  const [loading, setLoading] = useState(false);
  const [heatmapData, setHeatmapData] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);
  const [domain, setDomain] = useState(initialDomain);

  // Research areas and parameters for the heatmap
  const researchAreas = [
    'RNA editing',
    'RNA splicing',
    'RNA interference',
    'CRISPR',
    'RNA structure',
    'RNA therapeutics',
    'RNA sequencing',
    'lncRNA',
    'RNA metabolism',
    'RNA localization'
  ];

  const parameters = [
    'Temperature',
    'Concentration',
    'Time',
    'Cell type',
    'Organism',
    'Technique',
    'pH',
    'Buffer'
  ];

  useEffect(() => {
    if (domain) {
      fetchHeatmapData();
    }
  }, [domain]);

  const fetchHeatmapData = async () => {
    setLoading(true);
    try {
      const response = await analyzeGaps({
        domain: domain || 'all',
        analysis_type: 'comprehensive',
        include_opportunities: false
      });

      // Process data for heatmap
      const processedData = processHeatmapData(response);
      setHeatmapData(processedData);
    } catch (error) {
      console.error('Error fetching heatmap data:', error);
    }
    setLoading(false);
  };

  const processHeatmapData = (response) => {
    // Create a matrix of coverage scores
    const matrix = [];
    const { coverage_analysis, unexplored_combinations } = response;

    // Initialize matrix with base coverage
    for (let i = 0; i < researchAreas.length; i++) {
      matrix[i] = [];
      for (let j = 0; j < parameters.length; j++) {
        // Base score from coverage analysis
        const areaName = researchAreas[i];
        const paramName = parameters[j].toLowerCase();
        
        const areaCount = coverage_analysis?.research_areas?.areas?.[areaName] || 0;
        const paramCount = coverage_analysis?.parameter_space?.parameters?.[paramName]?.length || 0;
        
        // Calculate coverage score (0-1)
        const baseScore = Math.min((areaCount * paramCount) / 100, 1);
        
        matrix[i][j] = {
          value: baseScore,
          area: areaName,
          parameter: parameters[j],
          documentCount: areaCount,
          parameterVariants: paramCount,
          gaps: []
        };
      }
    }

    // Add gap information
    if (unexplored_combinations) {
      unexplored_combinations.forEach(combo => {
        // Find matching cells and mark as having gaps
        const comboParams = Object.keys(combo.combination);
        
        researchAreas.forEach((area, i) => {
          parameters.forEach((param, j) => {
            if (comboParams.some(p => p.toLowerCase().includes(param.toLowerCase()))) {
              matrix[i][j].gaps.push({
                type: 'unexplored_combination',
                impact: combo.impact_score,
                description: combo.rationale
              });
              // Reduce score based on gaps
              matrix[i][j].value *= (1 - combo.impact_score * 0.3);
            }
          });
        });
      }
    }

    return matrix;
  };

  const getColorForValue = (value) => {
    // Green (well-covered) to Red (gaps)
    if (value > 0.7) return 'bg-green-500';
    if (value > 0.5) return 'bg-yellow-500';
    if (value > 0.3) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const handleCellClick = (cell) => {
    setSelectedCell(cell);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="w-6 h-6" />
          Knowledge Gap Heatmap
        </CardTitle>
        <div className="flex gap-2 mt-4">
          <input
            type="text"
            placeholder="Enter domain (e.g., RNA editing)"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-md"
          />
          <Button onClick={fetchHeatmapData} disabled={loading}>
            <Search className="w-4 h-4 mr-2" />
            Analyze
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : heatmapData ? (
          <div className="space-y-4">
            {/* Heatmap Grid */}
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr>
                    <th className="px-2 py-1 text-xs font-medium text-gray-600"></th>
                    {parameters.map((param) => (
                      <th key={param} className="px-2 py-1 text-xs font-medium text-gray-600 vertical-text">
                        {param}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {researchAreas.map((area, i) => (
                    <tr key={area}>
                      <td className="px-2 py-1 text-xs font-medium text-gray-600 whitespace-nowrap">
                        {area}
                      </td>
                      {parameters.map((param, j) => {
                        const cell = heatmapData[i][j];
                        return (
                          <td key={`${i}-${j}`} className="p-1">
                            <div
                              className={`w-8 h-8 rounded cursor-pointer transition-all hover:scale-110 ${getColorForValue(cell.value)} opacity-${Math.round(cell.value * 100)}`}
                              onClick={() => handleCellClick(cell)}
                              title={`${area} × ${param}: ${(cell.value * 100).toFixed(0)}% covered`}
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 text-sm">
              <span className="font-medium">Coverage:</span>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                <span>High (&gt;70%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                <span>Medium (50-70%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-orange-500 rounded"></div>
                <span>Low (30-50%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-500 rounded"></div>
                <span>Very Low (&lt;30%)</span>
              </div>
            </div>

            {/* Selected Cell Details */}
            {selectedCell && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">
                  {selectedCell.area} × {selectedCell.parameter}
                </h4>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="font-medium">Coverage Score:</span>{' '}
                    {(selectedCell.value * 100).toFixed(1)}%
                  </p>
                  <p>
                    <span className="font-medium">Documents:</span>{' '}
                    {selectedCell.documentCount}
                  </p>
                  <p>
                    <span className="font-medium">Parameter Variants:</span>{' '}
                    {selectedCell.parameterVariants}
                  </p>
                  {selectedCell.gaps.length > 0 && (
                    <div>
                      <span className="font-medium">Identified Gaps:</span>
                      <ul className="mt-1 ml-4 list-disc">
                        {selectedCell.gaps.map((gap, idx) => (
                          <li key={idx} className="text-orange-600">
                            {gap.description} (Impact: {(gap.impact * 100).toFixed(0)}%)
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Info className="w-12 h-12 mx-auto mb-4" />
            <p>Enter a domain and click Analyze to view knowledge gaps</p>
          </div>
        )}

        <style jsx>{`
          .vertical-text {
            writing-mode: vertical-lr;
            text-orientation: mixed;
          }
          .opacity-10 { opacity: 0.1; }
          .opacity-20 { opacity: 0.2; }
          .opacity-30 { opacity: 0.3; }
          .opacity-40 { opacity: 0.4; }
          .opacity-50 { opacity: 0.5; }
          .opacity-60 { opacity: 0.6; }
          .opacity-70 { opacity: 0.7; }
          .opacity-80 { opacity: 0.8; }
          .opacity-90 { opacity: 0.9; }
          .opacity-100 { opacity: 1; }
        `}</style>
      </CardContent>
    </Card>
  );
};

export default KnowledgeGapHeatmap;