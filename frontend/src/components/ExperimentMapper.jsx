import React, { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { GlassCard, Button, Input, Loading, ColossalButton } from './enhanced';
import { Calendar, ChevronDown, ChevronUp, Download, Filter, Plus, Trash2, BarChart3, Network, Clock, TrendingUp } from 'lucide-react';
import { mapExperiments, formatExperimentData, extractKeyInsights, generateSampleExperiments } from '../api/experiments';
import toast from 'react-hot-toast';

const ExperimentMapper = () => {
  const [experiments, setExperiments] = useState([]);
  const [showForm, setShowForm] = useState(true);
  const [currentExperiment, setCurrentExperiment] = useState({
    type: '',
    targetLocus: '',
    variables: [{ name: '', value: '' }],
    conditions: [{ name: '', value: '' }],
    outcomes: [{ metric: '', value: '', unit: '' }],
    date: new Date().toISOString().split('T')[0],
    success: true
  });
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [viewMode, setViewMode] = useState('graph'); // graph, timeline, factors, patterns
  const [filterFactor, setFilterFactor] = useState('');
  const graphRef = useRef();

  // Process API analysis results for visualization
  const processAnalysisResults = (apiResponse, originalExperiments) => {
    const nodes = [];
    const links = [];
    
    // Add experiment nodes
    originalExperiments.forEach(exp => {
      nodes.push({
        id: `exp-${exp.id}`,
        name: `${exp.type} - ${exp.targetLocus}`,
        type: 'experiment',
        success: exp.success,
        data: exp
      });
      
      // Add variable nodes
      exp.variables.forEach(variable => {
        const nodeId = `var-${variable.name}-${variable.value}`;
        if (!nodes.find(n => n.id === nodeId)) {
          nodes.push({
            id: nodeId,
            name: `${variable.name}: ${variable.value}`,
            type: 'variable',
            factor: variable.name
          });
        }
        links.push({
          source: `exp-${exp.id}`,
          target: nodeId,
          type: 'variable'
        });
      });
      
      // Add condition nodes
      exp.conditions.forEach(condition => {
        const nodeId = `cond-${condition.name}-${condition.value}`;
        if (!nodes.find(n => n.id === nodeId)) {
          nodes.push({
            id: nodeId,
            name: `${condition.name}: ${condition.value}${condition.unit || ''}`,
            type: 'condition',
            factor: condition.name
          });
        }
        links.push({
          source: `exp-${exp.id}`,
          target: nodeId,
          type: 'condition'
        });
      });
    });
    
    setGraphData({ nodes, links });
    
    // Process analysis results
    const factorInfluence = apiResponse.factor_analysis?.top_factors?.map(factor => [
      factor.factor_name,
      {
        influenceScore: factor.importance_score * 100,
        successRate: factor.success_correlation * 100,
        avgOutcome: factor.average_outcome || 0,
        total: factor.occurrences || 0
      }
    ]) || [];
    
    const patterns = [];
    
    // Add success patterns
    if (apiResponse.patterns?.success_patterns?.length > 0) {
      patterns.push(...apiResponse.patterns.success_patterns.map(p => ({
        type: 'success',
        description: p,
        confidence: 0.8
      })));
    }
    
    // Add failure patterns
    if (apiResponse.patterns?.failure_patterns?.length > 0) {
      patterns.push(...apiResponse.patterns.failure_patterns.map(p => ({
        type: 'failure',
        description: p,
        confidence: 0.7
      })));
    }
    
    // Add correlations
    if (apiResponse.correlations?.length > 0) {
      patterns.push(...apiResponse.correlations.map(c => ({
        type: 'correlation',
        description: `${c.factor1} correlates with ${c.factor2} (r=${c.correlation.toFixed(2)})`,
        confidence: Math.abs(c.correlation)
      })));
    }
    
    setAnalysisResults({
      factorInfluence,
      patterns,
      recommendations: [
        ...(apiResponse.recommendations?.immediate_actions || []),
        ...(apiResponse.recommendations?.ai_insights || [])
      ],
      confoundingVariables: apiResponse.recommendations?.potential_confounders || []
    });
    
    setLoading(false);
  };
  
  // Generate sample data
  const generateSampleData = () => {
    const sampleExperiments = generateSampleExperiments('CRISPR');
    const formattedExperiments = [
      {
        id: 1,
        type: 'CRISPR-Cas9',
        targetLocus: 'BRCA1',
        variables: [
          { name: 'Cas Variant', value: 'SpCas9' },
          { name: 'Guide RNA', value: 'gRNA-BRCA1-1' },
          { name: 'PAM Sequence', value: 'NGG' }
        ],
        conditions: [
          { name: 'Temperature', value: '37', unit: '°C' },
          { name: 'Incubation Time', value: '48', unit: 'hours' },
          { name: 'Transfection Method', value: 'Lipofectamine' }
        ],
        outcomes: [
          { metric: 'Editing Efficiency', value: '85', unit: '%' },
          { metric: 'Off-target Events', value: '2', unit: 'sites' }
        ],
        date: '2024-01-15',
        success: true
      },
      {
        id: 2,
        type: 'CRISPR-Cas9',
        targetLocus: 'BRCA1',
        variables: [
          { name: 'Cas Variant', value: 'SpCas9-HF1' },
          { name: 'Guide RNA', value: 'gRNA-BRCA1-1' },
          { name: 'PAM Sequence', value: 'NGG' }
        ],
        conditions: [
          { name: 'Temperature', value: '37', unit: '°C' },
          { name: 'Incubation Time', value: '72', unit: 'hours' },
          { name: 'Transfection Method', value: 'Electroporation' }
        ],
        outcomes: [
          { metric: 'Editing Efficiency', value: '92', unit: '%' },
          { metric: 'Off-target Events', value: '0', unit: 'sites' }
        ],
        date: '2024-01-22',
        success: true
      },
      {
        id: 3,
        type: 'Base Editing',
        targetLocus: 'TP53',
        variables: [
          { name: 'Editor', value: 'ABE8e' },
          { name: 'Guide RNA', value: 'gRNA-TP53-R175H' },
          { name: 'PAM Variant', value: 'SpRY' }
        ],
        conditions: [
          { name: 'Temperature', value: '34', unit: '°C' },
          { name: 'Incubation Time', value: '96', unit: 'hours' },
          { name: 'Cell Type', value: 'HEK293T' }
        ],
        outcomes: [
          { metric: 'Base Editing Efficiency', value: '78', unit: '%' },
          { metric: 'Product Purity', value: '95', unit: '%' }
        ],
        date: '2024-02-10',
        success: true
      },
      {
        id: 4,
        type: 'Prime Editing',
        targetLocus: 'CFTR',
        variables: [
          { name: 'Editor', value: 'PE3' },
          { name: 'pegRNA', value: 'pegRNA-CFTR-F508del' },
          { name: 'RT Template Length', value: '13', unit: 'nt' }
        ],
        conditions: [
          { name: 'Temperature', value: '37', unit: '°C' },
          { name: 'Incubation Time', value: '120', unit: 'hours' },
          { name: 'Enhancer', value: 'MLH1dn' }
        ],
        outcomes: [
          { metric: 'Prime Editing Efficiency', value: '45', unit: '%' },
          { metric: 'Indel Frequency', value: '3', unit: '%' }
        ],
        date: '2024-03-05',
        success: false
      }
    ].map((exp, index) => ({
      ...exp,
      id: exp.id || index + 1,
      success: exp.outcomes[0]?.value ? parseFloat(exp.outcomes[0].value) > 60 : exp.success
    }));

    setExperiments(formattedExperiments);
    setTimeout(() => analyzeExperiments([...formattedExperiments]), 100);
  };

  // Add field to arrays
  const addField = (fieldType) => {
    setCurrentExperiment(prev => ({
      ...prev,
      [fieldType]: [...prev[fieldType], fieldType === 'variables' || fieldType === 'conditions' 
        ? { name: '', value: '', unit: '' } 
        : { metric: '', value: '', unit: '' }]
    }));
  };

  // Remove field from arrays
  const removeField = (fieldType, index) => {
    setCurrentExperiment(prev => ({
      ...prev,
      [fieldType]: prev[fieldType].filter((_, i) => i !== index)
    }));
  };

  // Update field values
  const updateField = (fieldType, index, field, value) => {
    setCurrentExperiment(prev => ({
      ...prev,
      [fieldType]: prev[fieldType].map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  // Add experiment
  const addExperiment = () => {
    const newExperiment = {
      ...currentExperiment,
      id: Date.now()
    };
    const updatedExperiments = [...experiments, newExperiment];
    setExperiments(updatedExperiments);
    
    // Reset form
    setCurrentExperiment({
      type: '',
      targetLocus: '',
      variables: [{ name: '', value: '' }],
      conditions: [{ name: '', value: '' }],
      outcomes: [{ metric: '', value: '', unit: '' }],
      date: new Date().toISOString().split('T')[0],
      success: true
    });

    // Analyze if we have enough experiments
    if (updatedExperiments.length >= 2) {
      analyzeExperiments(updatedExperiments);
    }
  };

  // Analyze experiments
  const analyzeExperiments = async (experimentsToAnalyze) => {
    setLoading(true);
    
    try {
      // Format experiments for API
      const formattedExperiments = experimentsToAnalyze.map(exp => ({
        experiment_id: exp.id?.toString() || `exp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        experiment_type: exp.type,
        target_locus: exp.targetLocus,
        variables: exp.variables.reduce((acc, v) => ({
          ...acc,
          [v.name.toLowerCase().replace(/ /g, '_')]: v.value
        }), {}),
        conditions: exp.conditions.reduce((acc, c) => ({
          ...acc,
          [c.name.toLowerCase().replace(/ /g, '_')]: `${c.value}${c.unit || ''}`
        }), {}),
        outcomes: exp.outcomes.reduce((acc, o) => ({
          ...acc,
          [o.metric.toLowerCase().replace(/ /g, '_')]: parseFloat(o.value) || o.value
        }), {}),
        success_metrics: {
          overall_success: exp.success,
          primary_metric: exp.outcomes[0] ? parseFloat(exp.outcomes[0].value) : 0
        },
        date_performed: exp.date
      }));
      
      // Call API
      const apiResponse = await mapExperiments(formattedExperiments);
      
      if (apiResponse.success) {
        // Extract insights
        const insights = extractKeyInsights(apiResponse);
        
        // Process API response for visualization
        processAnalysisResults(apiResponse, experimentsToAnalyze);
        
        toast.success('Experiment analysis complete!');
      } else {
        throw new Error(apiResponse.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Error analyzing experiments:', error);
      toast.error('Using demo analysis due to API error');
      
      // Fallback to demo analysis
      setTimeout(() => {
      // Create graph data
      const nodes = [];
      const links = [];
      const factorInfluence = {};
      const patterns = [];

      // Add experiment nodes
      experimentsToAnalyze.forEach(exp => {
        nodes.push({
          id: `exp-${exp.id}`,
          name: `${exp.type} - ${exp.targetLocus}`,
          type: 'experiment',
          success: exp.success,
          data: exp
        });

        // Add factor nodes and calculate influence
        exp.variables.forEach(variable => {
          const nodeId = `var-${variable.name}-${variable.value}`;
          if (!nodes.find(n => n.id === nodeId)) {
            nodes.push({
              id: nodeId,
              name: `${variable.name}: ${variable.value}`,
              type: 'variable',
              factor: variable.name
            });
          }
          links.push({
            source: `exp-${exp.id}`,
            target: nodeId,
            type: 'variable'
          });

          // Track influence
          const key = `${variable.name}: ${variable.value}`;
          if (!factorInfluence[key]) {
            factorInfluence[key] = { success: 0, total: 0, avgOutcome: 0 };
          }
          factorInfluence[key].total++;
          if (exp.success) factorInfluence[key].success++;
          
          const efficiency = exp.outcomes.find(o => o.metric.includes('Efficiency'));
          if (efficiency) {
            factorInfluence[key].avgOutcome += parseFloat(efficiency.value);
          }
        });

        exp.conditions.forEach(condition => {
          const nodeId = `cond-${condition.name}-${condition.value}`;
          if (!nodes.find(n => n.id === nodeId)) {
            nodes.push({
              id: nodeId,
              name: `${condition.name}: ${condition.value}${condition.unit ? condition.unit : ''}`,
              type: 'condition',
              factor: condition.name
            });
          }
          links.push({
            source: `exp-${exp.id}`,
            target: nodeId,
            type: 'condition'
          });
        });
      });

      // Calculate final influence scores
      Object.keys(factorInfluence).forEach(key => {
        const factor = factorInfluence[key];
        factor.successRate = (factor.success / factor.total) * 100;
        factor.avgOutcome = factor.avgOutcome / factor.total;
        factor.influenceScore = (factor.successRate * 0.6) + (factor.avgOutcome * 0.4);
      });

      // Detect patterns
      const casVariants = {};
      experimentsToAnalyze.forEach(exp => {
        const casVar = exp.variables.find(v => v.name === 'Cas Variant');
        if (casVar) {
          if (!casVariants[casVar.value]) {
            casVariants[casVar.value] = [];
          }
          const efficiency = exp.outcomes.find(o => o.metric.includes('Efficiency'));
          if (efficiency) {
            casVariants[casVar.value].push(parseFloat(efficiency.value));
          }
        }
      });

      Object.entries(casVariants).forEach(([variant, efficiencies]) => {
        if (efficiencies.length > 1) {
          const avg = efficiencies.reduce((a, b) => a + b, 0) / efficiencies.length;
          patterns.push({
            type: 'performance',
            description: `${variant} shows average efficiency of ${avg.toFixed(1)}%`,
            confidence: 0.8
          });
        }
      });

      // Temperature correlation
      const tempData = experimentsToAnalyze
        .map(exp => {
          const temp = exp.conditions.find(c => c.name === 'Temperature');
          const efficiency = exp.outcomes.find(o => o.metric.includes('Efficiency'));
          return temp && efficiency ? { temp: parseFloat(temp.value), eff: parseFloat(efficiency.value) } : null;
        })
        .filter(Boolean);

      if (tempData.length > 2) {
        patterns.push({
          type: 'correlation',
          description: 'Temperature appears to influence editing efficiency',
          confidence: 0.7
        });
      }

      setGraphData({ nodes, links });
      setAnalysisResults({
        factorInfluence: Object.entries(factorInfluence)
          .sort((a, b) => b[1].influenceScore - a[1].influenceScore)
          .slice(0, 5),
        patterns,
        recommendations: [
          'Consider using SpCas9-HF1 for higher specificity',
          'Longer incubation times (72h+) correlate with better outcomes',
          'Electroporation shows promise for difficult targets',
          'Monitor temperature stability for consistent results'
        ],
        confoundingVariables: ['Cell passage number', 'Media batch', 'Operator experience']
      });

      setLoading(false);
    }, 1500);
  };

  // Export results
  const exportResults = () => {
    const data = {
      experiments,
      analysis: analysisResults,
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `experiment-mapping-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Filter graph data
  useEffect(() => {
    if (filterFactor && graphData.nodes.length > 0) {
      const filteredNodes = graphData.nodes.filter(node => 
        node.type === 'experiment' || 
        (node.factor && node.factor.toLowerCase().includes(filterFactor.toLowerCase()))
      );
      
      const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
      const filteredLinks = graphData.links.filter(link => 
        filteredNodeIds.has(link.source.id || link.source) && 
        filteredNodeIds.has(link.target.id || link.target)
      );

      setGraphData({ nodes: filteredNodes, links: filteredLinks });
    } else if (!filterFactor && experiments.length > 0) {
      analyzeExperiments(experiments);
    }
  }, [filterFactor]);

  return (
    <div className="experiment-mapper p-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
          Experiment Mapper
        </h1>
        <p className="text-gray-400">Map and analyze your CRISPR experiments to discover patterns</p>
      </div>

      {/* Input Form */}
      <GlassCard className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">Add Experiment</h2>
          <div className="flex gap-2">
            <Button
              onClick={generateSampleData}
              className="bg-purple-500/20 hover:bg-purple-500/30 text-purple-300"
            >
              Generate Sample Data
            </Button>
            <Button
              onClick={() => setShowForm(!showForm)}
              className="bg-gray-500/20 hover:bg-gray-500/30"
            >
              {showForm ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </Button>
          </div>
        </div>

        {showForm && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                placeholder="Experiment Type (e.g., CRISPR-Cas9)"
                value={currentExperiment.type}
                onChange={(e) => setCurrentExperiment(prev => ({ ...prev, type: e.target.value }))}
              />
              <Input
                placeholder="Target Locus (e.g., BRCA1)"
                value={currentExperiment.targetLocus}
                onChange={(e) => setCurrentExperiment(prev => ({ ...prev, targetLocus: e.target.value }))}
              />
            </div>

            {/* Variables */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium text-gray-300">Variables</h3>
                <Button
                  onClick={() => addField('variables')}
                  className="bg-green-500/20 hover:bg-green-500/30 text-green-300 p-1"
                >
                  <Plus size={16} />
                </Button>
              </div>
              {currentExperiment.variables.map((variable, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <Input
                    placeholder="Variable name"
                    value={variable.name}
                    onChange={(e) => updateField('variables', index, 'name', e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    placeholder="Value"
                    value={variable.value}
                    onChange={(e) => updateField('variables', index, 'value', e.target.value)}
                    className="flex-1"
                  />
                  {currentExperiment.variables.length > 1 && (
                    <Button
                      onClick={() => removeField('variables', index)}
                      className="bg-red-500/20 hover:bg-red-500/30 text-red-300 p-2"
                    >
                      <Trash2 size={16} />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            {/* Conditions */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium text-gray-300">Conditions</h3>
                <Button
                  onClick={() => addField('conditions')}
                  className="bg-green-500/20 hover:bg-green-500/30 text-green-300 p-1"
                >
                  <Plus size={16} />
                </Button>
              </div>
              {currentExperiment.conditions.map((condition, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <Input
                    placeholder="Condition name"
                    value={condition.name}
                    onChange={(e) => updateField('conditions', index, 'name', e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    placeholder="Value"
                    value={condition.value}
                    onChange={(e) => updateField('conditions', index, 'value', e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    placeholder="Unit"
                    value={condition.unit}
                    onChange={(e) => updateField('conditions', index, 'unit', e.target.value)}
                    className="w-24"
                  />
                  {currentExperiment.conditions.length > 1 && (
                    <Button
                      onClick={() => removeField('conditions', index)}
                      className="bg-red-500/20 hover:bg-red-500/30 text-red-300 p-2"
                    >
                      <Trash2 size={16} />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            {/* Outcomes */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium text-gray-300">Outcomes</h3>
                <Button
                  onClick={() => addField('outcomes')}
                  className="bg-green-500/20 hover:bg-green-500/30 text-green-300 p-1"
                >
                  <Plus size={16} />
                </Button>
              </div>
              {currentExperiment.outcomes.map((outcome, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <Input
                    placeholder="Metric"
                    value={outcome.metric}
                    onChange={(e) => updateField('outcomes', index, 'metric', e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    placeholder="Value"
                    value={outcome.value}
                    onChange={(e) => updateField('outcomes', index, 'value', e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    placeholder="Unit"
                    value={outcome.unit}
                    onChange={(e) => updateField('outcomes', index, 'unit', e.target.value)}
                    className="w-24"
                  />
                  {currentExperiment.outcomes.length > 1 && (
                    <Button
                      onClick={() => removeField('outcomes', index)}
                      className="bg-red-500/20 hover:bg-red-500/30 text-red-300 p-2"
                    >
                      <Trash2 size={16} />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            {/* Date and Success */}
            <div className="flex gap-4 items-center">
              <Input
                type="date"
                value={currentExperiment.date}
                onChange={(e) => setCurrentExperiment(prev => ({ ...prev, date: e.target.value }))}
                className="flex-1"
              />
              <label className="flex items-center gap-2 text-gray-300">
                <input
                  type="checkbox"
                  checked={currentExperiment.success}
                  onChange={(e) => setCurrentExperiment(prev => ({ ...prev, success: e.target.checked }))}
                  className="rounded border-gray-600 bg-gray-700 text-purple-500"
                />
                Successful
              </label>
            </div>

            <ColossalButton onClick={addExperiment} className="w-full">
              Add Experiment
            </ColossalButton>
          </div>
        )}
      </GlassCard>

      {/* View Mode Selector */}
      {experiments.length > 0 && (
        <div className="flex gap-2 mb-6">
          <Button
            onClick={() => setViewMode('graph')}
            className={`${viewMode === 'graph' ? 'bg-purple-500/30 text-purple-300' : 'bg-gray-700/50'}`}
          >
            <Network size={16} className="mr-2" />
            Knowledge Graph
          </Button>
          <Button
            onClick={() => setViewMode('factors')}
            className={`${viewMode === 'factors' ? 'bg-purple-500/30 text-purple-300' : 'bg-gray-700/50'}`}
          >
            <BarChart3 size={16} className="mr-2" />
            Factor Analysis
          </Button>
          <Button
            onClick={() => setViewMode('timeline')}
            className={`${viewMode === 'timeline' ? 'bg-purple-500/30 text-purple-300' : 'bg-gray-700/50'}`}
          >
            <Clock size={16} className="mr-2" />
            Timeline
          </Button>
          <Button
            onClick={() => setViewMode('patterns')}
            className={`${viewMode === 'patterns' ? 'bg-purple-500/30 text-purple-300' : 'bg-gray-700/50'}`}
          >
            <TrendingUp size={16} className="mr-2" />
            Patterns
          </Button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <Loading />
        </div>
      )}

      {/* Knowledge Graph View */}
      {!loading && viewMode === 'graph' && graphData.nodes.length > 0 && (
        <GlassCard className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Experiment Knowledge Graph</h2>
            <div className="flex gap-2">
              <Input
                placeholder="Filter by factor..."
                value={filterFactor}
                onChange={(e) => setFilterFactor(e.target.value)}
                className="w-48"
                icon={<Filter size={16} />}
              />
              <Button
                onClick={exportResults}
                className="bg-blue-500/20 hover:bg-blue-500/30 text-blue-300"
              >
                <Download size={16} className="mr-2" />
                Export
              </Button>
            </div>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4" style={{ height: '500px' }}>
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeAutoColorBy="type"
              nodeCanvasObject={(node, ctx, globalScale) => {
                const label = node.name;
                const fontSize = 12/globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                
                // Draw node
                if (node.type === 'experiment') {
                  ctx.fillStyle = node.success ? '#10b981' : '#ef4444';
                } else if (node.type === 'variable') {
                  ctx.fillStyle = '#8b5cf6';
                } else {
                  ctx.fillStyle = '#3b82f6';
                }
                
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.type === 'experiment' ? 8 : 5, 0, 2 * Math.PI, false);
                ctx.fill();
                
                // Draw label
                ctx.fillStyle = '#e5e7eb';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(label, node.x, node.y + 15);
              }}
              linkColor={() => '#4b5563'}
              linkWidth={2}
              onNodeClick={(node) => setSelectedNode(node)}
              enableZoomPanInteraction={true}
              enableNodeDrag={true}
            />
          </div>

          {/* Node Details */}
          {selectedNode && (
            <div className="mt-4 p-4 bg-gray-800/50 rounded-lg">
              <h3 className="text-lg font-semibold text-white mb-2">{selectedNode.name}</h3>
              {selectedNode.type === 'experiment' && selectedNode.data && (
                <div className="space-y-2 text-sm text-gray-300">
                  <p><span className="text-gray-500">Type:</span> {selectedNode.data.type}</p>
                  <p><span className="text-gray-500">Target:</span> {selectedNode.data.targetLocus}</p>
                  <p><span className="text-gray-500">Date:</span> {selectedNode.data.date}</p>
                  <p><span className="text-gray-500">Status:</span> 
                    <span className={selectedNode.data.success ? 'text-green-400' : 'text-red-400'}>
                      {selectedNode.data.success ? ' Successful' : ' Failed'}
                    </span>
                  </p>
                </div>
              )}
            </div>
          )}
        </GlassCard>
      )}

      {/* Factor Analysis View */}
      {!loading && viewMode === 'factors' && analysisResults && (
        <GlassCard>
          <h2 className="text-xl font-semibold text-white mb-4">Factor Influence Analysis</h2>
          <div className="space-y-4">
            {analysisResults.factorInfluence.map(([factor, data], index) => (
              <div key={factor} className="p-4 bg-gray-800/50 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-medium text-white">{factor}</h3>
                  <span className="text-purple-400 font-semibold">
                    Score: {data.influenceScore.toFixed(1)}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Success Rate</p>
                    <p className="text-green-400">{data.successRate.toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Avg Outcome</p>
                    <p className="text-blue-400">{data.avgOutcome.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Experiments</p>
                    <p className="text-gray-300">{data.total}</p>
                  </div>
                </div>
                <div className="mt-2 bg-gray-700/50 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${data.influenceScore}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Timeline View */}
      {!loading && viewMode === 'timeline' && experiments.length > 0 && (
        <GlassCard>
          <h2 className="text-xl font-semibold text-white mb-4">Experiment Timeline</h2>
          <div className="space-y-4">
            {experiments
              .sort((a, b) => new Date(a.date) - new Date(b.date))
              .map((exp, index) => (
                <div key={exp.id} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`w-4 h-4 rounded-full ${exp.success ? 'bg-green-500' : 'bg-red-500'}`} />
                    {index < experiments.length - 1 && (
                      <div className="w-0.5 h-20 bg-gray-600" />
                    )}
                  </div>
                  <div className="flex-1 pb-8">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-medium text-white">
                        {exp.type} - {exp.targetLocus}
                      </h3>
                      <span className="text-sm text-gray-400">
                        <Calendar size={14} className="inline mr-1" />
                        {new Date(exp.date).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="text-sm text-gray-300 space-y-1">
                      {exp.outcomes.map((outcome, i) => (
                        <p key={i}>
                          {outcome.metric}: {outcome.value}{outcome.unit}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </GlassCard>
      )}

      {/* Patterns View */}
      {!loading && viewMode === 'patterns' && analysisResults && (
        <div className="space-y-6">
          <GlassCard>
            <h2 className="text-xl font-semibold text-white mb-4">Detected Patterns</h2>
            <div className="space-y-3">
              {analysisResults.patterns.map((pattern, index) => (
                <div key={index} className="p-4 bg-gray-800/50 rounded-lg">
                  <div className="flex justify-between items-start">
                    <p className="text-gray-300">{pattern.description}</p>
                    <span className="text-xs text-purple-400 bg-purple-500/20 px-2 py-1 rounded">
                      {(pattern.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="text-xl font-semibold text-white mb-4">AI Recommendations</h2>
            <div className="space-y-3">
              {analysisResults.recommendations.map((rec, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2" />
                  <p className="text-gray-300">{rec}</p>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="text-xl font-semibold text-white mb-4">Potential Confounding Variables</h2>
            <div className="flex flex-wrap gap-2">
              {analysisResults.confoundingVariables.map((variable, index) => (
                <span 
                  key={index}
                  className="px-3 py-1 bg-yellow-500/20 text-yellow-300 rounded-full text-sm"
                >
                  {variable}
                </span>
              ))}
            </div>
          </GlassCard>
        </div>
      )}

      {/* Empty State */}
      {experiments.length === 0 && !loading && (
        <GlassCard className="text-center py-12">
          <p className="text-gray-400 mb-4">No experiments added yet</p>
          <ColossalButton onClick={generateSampleData}>
            Generate Sample Data
          </ColossalButton>
        </GlassCard>
      )}
    </div>
  );
};
}

export default ExperimentMapper;