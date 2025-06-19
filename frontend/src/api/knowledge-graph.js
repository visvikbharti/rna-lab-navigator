import { apiRequest } from './config';

export const knowledgeGraphApi = {
  // Get graph overview statistics
  getOverview: () => 
    apiRequest('/api/knowledge-graph/overview/'),
  
  // Trigger connection discovery
  discoverConnections: () =>
    apiRequest('/api/knowledge-graph/discover/', {
      method: 'POST'
    }),
  
  // Trigger clustering
  clusterNodes: (params = {}) =>
    apiRequest('/api/knowledge-graph/cluster/', {
      method: 'POST',
      body: JSON.stringify(params)
    }),
  
  // Get temporal evolution data
  getTemporalEvolution: (params) =>
    apiRequest('/api/knowledge-graph/temporal/', {
      params
    }),
  
  // Search nodes
  searchNodes: (query, nodeTypes = []) =>
    apiRequest('/api/knowledge-graph/search/', {
      method: 'POST',
      body: JSON.stringify({ query, node_types: nodeTypes })
    })
};