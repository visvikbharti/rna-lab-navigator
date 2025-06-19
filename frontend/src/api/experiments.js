import axios from 'axios';

// Base URL for experiments API
const API_URL = '/api/experiments';

/**
 * Map and analyze a series of experiments
 * 
 * @param {Array} experiments - Array of experiment data
 * @param {string} analysisFocus - Optional focus for analysis
 * @returns {Promise} - Promise resolving to mapping analysis
 */
export const mapExperiments = async (experiments, analysisFocus = null) => {
  try {
    const response = await axios.post(`${API_URL}/map/`, {
      experiments,
      analysis_focus: analysisFocus
    }, {
      timeout: 30000 // 30 seconds for complex analysis
    });
    
    return response.data;
  } catch (error) {
    console.error('Error mapping experiments:', error);
    
    if (error.response) {
      throw new Error(error.response.data?.error || 'Failed to map experiments');
    } else if (error.request) {
      throw new Error('No response from server. Please check your connection.');
    } else {
      throw error;
    }
  }
};

/**
 * Analyze a single experiment
 * 
 * @param {Object} experiment - Single experiment data
 * @param {Array} compareWithIds - Optional experiment IDs to compare with
 * @returns {Promise} - Promise resolving to analysis
 */
export const analyzeSingleExperiment = async (experiment, compareWithIds = []) => {
  try {
    const response = await axios.post(`${API_URL}/analyze-single/`, {
      experiment,
      compare_with: compareWithIds
    });
    
    return response.data;
  } catch (error) {
    console.error('Error analyzing experiment:', error);
    
    if (error.response) {
      throw new Error(error.response.data?.error || 'Failed to analyze experiment');
    } else {
      throw error;
    }
  }
};

/**
 * Quick factor analysis
 * 
 * @param {Array} experiments - Array of experiment data
 * @param {string} targetFactor - Optional specific factor to analyze
 * @returns {Promise} - Promise resolving to factor analysis
 */
export const quickFactorAnalysis = async (experiments, targetFactor = null) => {
  try {
    const response = await axios.post(`${API_URL}/quick-factor-analysis/`, {
      experiments,
      target_factor: targetFactor
    });
    
    return response.data;
  } catch (error) {
    console.error('Error in factor analysis:', error);
    
    if (error.response) {
      throw new Error(error.response.data?.error || 'Failed to analyze factors');
    } else {
      throw error;
    }
  }
};

/**
 * Get experiment mapping feature status
 * 
 * @returns {Promise} - Promise resolving to feature status
 */
export const getExperimentMappingStatus = async () => {
  try {
    const response = await axios.get(`${API_URL}/status/`);
    return response.data;
  } catch (error) {
    console.error('Error getting status:', error);
    throw error;
  }
};

/**
 * Helper function to format experiment data
 * 
 * @param {Object} rawData - Raw experiment data
 * @returns {Object} - Formatted experiment data
 */
export const formatExperimentData = (rawData) => {
  return {
    experiment_id: rawData.id || `exp_${Date.now()}`,
    experiment_type: rawData.type || '',
    target_locus: rawData.target || '',
    variables: rawData.variables || {},
    conditions: rawData.conditions || {},
    outcomes: rawData.outcomes || {},
    success_metrics: rawData.metrics || {},
    researcher: rawData.researcher || '',
    date_performed: rawData.date || new Date().toISOString(),
    notes: rawData.notes || ''
  };
};

/**
 * Helper function to generate sample experiments for demo
 * 
 * @param {string} experimentType - Type of experiments to generate
 * @returns {Array} - Array of sample experiments
 */
export const generateSampleExperiments = (experimentType = 'IVC assay') => {
  const casVariants = ['SpCas9', 'FnCas9', 'SaCas9', 'AsCas12a'];
  const guides = ['sgRNA-1', 'sgRNA-2', 'sgRNA-3'];
  const targets = ['AAVS1', 'CCR5', 'IL2RG'];
  
  const experiments = [];
  
  for (let i = 0; i < 8; i++) {
    const casVariant = casVariants[i % casVariants.length];
    const guide = guides[Math.floor(i / casVariants.length) % guides.length];
    const target = targets[Math.floor(i / (casVariants.length * guides.length)) % targets.length];
    
    // Simulate different success rates for different variants
    const baseEfficiency = casVariant === 'FnCas9' ? 0.9 : casVariant === 'SpCas9' ? 0.85 : 0.75;
    const efficiency = baseEfficiency + (Math.random() * 0.1 - 0.05);
    const specificity = 0.95 + (Math.random() * 0.04);
    
    experiments.push({
      experiment_id: `exp${String(i + 1).padStart(3, '0')}`,
      experiment_type: experimentType,
      target_locus: target,
      variables: {
        cas_variant: casVariant,
        guide_rna: guide,
        pam: casVariant.includes('Cas9') ? 'NGG' : 'TTTN',
        delivery_method: i % 2 === 0 ? 'transfection' : 'electroporation'
      },
      conditions: {
        temperature: 37,
        incubation_time: '48h',
        cell_type: 'HEK293T',
        confluence: `${70 + i * 2}%`
      },
      outcomes: {
        cleavage_efficiency: efficiency,
        off_target_rate: 1 - specificity,
        cell_viability: 0.85 + Math.random() * 0.1
      },
      success_metrics: {
        efficiency: efficiency,
        specificity: specificity,
        overall_score: (efficiency + specificity) / 2
      },
      researcher: i < 4 ? 'Dr. Smith' : 'Dr. Johnson',
      date_performed: new Date(Date.now() - (7 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      notes: `Experiment ${i + 1} of the ${casVariant} series`
    });
  }
  
  return experiments;
};

/**
 * Helper to extract key insights from mapping results
 * 
 * @param {Object} mappingResult - Result from mapExperiments
 * @returns {Object} - Key insights
 */
export const extractKeyInsights = (mappingResult) => {
  if (!mappingResult || !mappingResult.success) {
    return {
      topFactors: [],
      patterns: [],
      recommendations: []
    };
  }
  
  const insights = {
    topFactors: mappingResult.factor_analysis?.top_factors || [],
    patterns: [],
    recommendations: []
  };
  
  // Extract patterns
  const patterns = mappingResult.patterns || {};
  if (patterns.success_patterns?.length > 0) {
    insights.patterns.push({
      type: 'success',
      description: 'Common factors in successful experiments',
      details: patterns.success_patterns[0]
    });
  }
  
  if (patterns.failure_patterns?.length > 0) {
    insights.patterns.push({
      type: 'failure',
      description: 'Common factors in failed experiments',
      details: patterns.failure_patterns[0]
    });
  }
  
  // Extract recommendations
  const recs = mappingResult.recommendations || {};
  if (recs.immediate_actions?.length > 0) {
    insights.recommendations.push(...recs.immediate_actions);
  }
  
  if (recs.ai_insights?.length > 0) {
    insights.recommendations.push(...recs.ai_insights);
  }
  
  return insights;
};