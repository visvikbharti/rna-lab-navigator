import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlassPlusIcon,
  MagnifyingGlassMinusIcon,
  ArrowPathIcon,
  FunnelIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  SparklesIcon,
  ChartBarIcon,
  DocumentTextIcon,
  BeakerIcon,
  LinkIcon
} from '@heroicons/react/24/outline';
import { useWebSocket } from '../hooks/useWebSocket';
import { GlassCard, GradientText } from './enhanced';
import Loading from './enhanced/Loading';

const nodeTypeColors = {
  paper: '#3B82F6',      // blue
  thesis: '#8B5CF6',     // purple
  protocol: '#10B981',   // green
  inventory: '#F59E0B',  // amber
  unknown: '#6B7280'     // gray
};

const connectionTypeStyles = {
  methodological: { stroke: '#8B5CF6', strokeDasharray: '5,5' },
  entity_based: { stroke: '#10B981', strokeDasharray: '0' },
  topic_related: { stroke: '#3B82F6', strokeDasharray: '3,3' },
  citation: { stroke: '#F59E0B', strokeDasharray: '0' },
  complementary: { stroke: '#14B8A6', strokeDasharray: '0' },
  contradictory: { stroke: '#EF4444', strokeDasharray: '8,4' }
};

function KnowledgeGraphExplorer({ initialNodeId = null, onNodeSelect }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [filterOptions, setFilterOptions] = useState({
    nodeTypes: ['paper', 'thesis', 'protocol', 'inventory'],
    connectionTypes: Object.keys(connectionTypeStyles),
    minDegree: 0
  });
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  
  // WebSocket connection
  const { connected, sendMessage, subscribe, unsubscribe } = useWebSocket();

  // D3 simulation reference
  const simulationRef = useRef(null);
  const zoomRef = useRef(null);

  useEffect(() => {
    // Update dimensions on resize
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: height - 100 }); // Leave space for controls
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!connected) return;

    // Subscribe to WebSocket events
    subscribe('graph_init', (data) => {
      setGraphData(data.data);
      setStats(data.data.stats);
      setLoading(false);
    });

    subscribe('graph_update', (data) => {
      setGraphData(data.data);
    });

    subscribe('new_connection', (data) => {
      // Add animation for new connection
      handleNewConnection(data.data);
    });

    subscribe('new_node', (data) => {
      // Add animation for new node
      handleNewNode(data.data);
    });

    subscribe('search_results', (data) => {
      setSearchResults(data.data);
    });

    subscribe('trend_data', (data) => {
      setTrends(data.data);
    });

    // Request initial data
    if (initialNodeId) {
      sendMessage({
        type: 'get_subgraph',
        node_id: initialNodeId,
        depth: 2
      });
    }

    // Request trends
    sendMessage({ type: 'get_trends' });

    return () => {
      unsubscribe('graph_init');
      unsubscribe('graph_update');
      unsubscribe('new_connection');
      unsubscribe('new_node');
      unsubscribe('search_results');
      unsubscribe('trend_data');
    };
  }, [connected, initialNodeId]);

  useEffect(() => {
    if (!graphData.nodes.length) return;

    // Initialize D3 visualization
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;

    // Create zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);
    zoomRef.current = zoom;

    // Create main group
    const g = svg.append('g');

    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force('link', d3.forceLink(graphData.edges)
        .id(d => d.id)
        .distance(d => 100 / (d.weight || 1)))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => d.degree * 5 + 20));

    simulationRef.current = simulation;

    // Filter data based on options
    const filteredNodes = graphData.nodes.filter(node => 
      filterOptions.nodeTypes.includes(node.type) &&
      node.degree >= filterOptions.minDegree
    );

    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = graphData.edges.filter(edge =>
      filteredNodeIds.has(edge.source.id || edge.source) &&
      filteredNodeIds.has(edge.target.id || edge.target) &&
      filterOptions.connectionTypes.includes(edge.type)
    );

    // Create links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(filteredEdges)
      .enter().append('line')
      .attr('stroke', d => connectionTypeStyles[d.type]?.stroke || '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.weight || 1))
      .attr('stroke-dasharray', d => connectionTypeStyles[d.type]?.strokeDasharray || '0');

    // Create nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(filteredNodes)
      .enter().append('g')
      .call(drag(simulation));

    // Add circles for nodes
    node.append('circle')
      .attr('r', d => Math.min(d.degree * 3 + 10, 40))
      .attr('fill', d => nodeTypeColors[d.type] || nodeTypeColors.unknown)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('mouseover', handleNodeHover)
      .on('mouseout', () => setHoveredNode(null))
      .on('click', handleNodeClick);

    // Add labels
    node.append('text')
      .text(d => d.label)
      .attr('x', 0)
      .attr('y', d => Math.min(d.degree * 3 + 10, 40) + 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#e5e7eb')
      .attr('pointer-events', 'none');

    // Add glow effect for important nodes
    const importantNodes = filteredNodes.filter(n => n.degree > 5);
    node.filter(n => importantNodes.includes(n))
      .append('circle')
      .attr('r', d => Math.min(d.degree * 3 + 10, 40) + 5)
      .attr('fill', 'none')
      .attr('stroke', d => nodeTypeColors[d.type] || nodeTypeColors.unknown)
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.3)
      .attr('class', 'pulse-animation');

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [graphData, filterOptions, dimensions]);

  // D3 drag behavior
  const drag = (simulation) => {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  };

  const handleNodeHover = (event, node) => {
    setHoveredNode(node);
  };

  const handleNodeClick = (event, node) => {
    setSelectedNode(node);
    if (onNodeSelect) {
      onNodeSelect(node);
    }
    
    // Request suggestions for this node
    sendMessage({
      type: 'get_suggestions',
      node_id: node.id
    });
  };

  const handleNewConnection = (connection) => {
    // Animate new connection
    const svg = d3.select(svgRef.current);
    const link = svg.select('.links')
      .append('line')
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)
      .attr('stroke-opacity', 0)
      .transition()
      .duration(1000)
      .attr('stroke-opacity', 1)
      .transition()
      .duration(500)
      .attr('stroke', connectionTypeStyles[connection.type]?.stroke || '#999')
      .attr('stroke-opacity', 0.6);
  };

  const handleNewNode = (node) => {
    // Animate new node
    const svg = d3.select(svgRef.current);
    const g = svg.select('.nodes')
      .append('g')
      .attr('transform', `translate(${dimensions.width / 2},${dimensions.height / 2})`)
      .attr('opacity', 0);

    g.append('circle')
      .attr('r', 0)
      .attr('fill', nodeTypeColors[node.type])
      .transition()
      .duration(1000)
      .attr('r', 20);

    g.transition()
      .duration(1000)
      .attr('opacity', 1);
  };

  const handleSearch = () => {
    if (searchQuery) {
      sendMessage({
        type: 'search_nodes',
        query: searchQuery
      });
    }
  };

  const handleZoom = (direction) => {
    const svg = d3.select(svgRef.current);
    const zoom = zoomRef.current;
    
    if (direction === 'in') {
      svg.transition().call(zoom.scaleBy, 1.3);
    } else if (direction === 'out') {
      svg.transition().call(zoom.scaleBy, 0.7);
    } else if (direction === 'reset') {
      svg.transition().call(zoom.transform, d3.zoomIdentity);
    }
  };

  const toggleFilter = (type, value) => {
    setFilterOptions(prev => ({
      ...prev,
      [type]: prev[type].includes(value)
        ? prev[type].filter(v => v !== value)
        : [...prev[type], value]
    }));
  };

  return (
    <div className="relative w-full h-full" ref={containerRef}>
      {/* Header Controls */}
      <div className="absolute top-0 left-0 right-0 z-10 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <GradientText className="text-2xl font-bold" gradient="cyber">
              Knowledge Graph Explorer
            </GradientText>
            
            {stats && (
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <span>{stats.total_nodes} nodes</span>
                <span>{stats.total_edges} connections</span>
                <span>{stats.average_degree.toFixed(1)} avg degree</span>
              </div>
            )}
          </div>

          {/* Search Bar */}
          <div className="flex items-center space-x-2">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search nodes..."
                className="pl-10 pr-4 py-2 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <MagnifyingGlassIcon className="absolute left-3 top-2.5 w-5 h-5 text-gray-500" />
            </div>
            
            {/* Zoom Controls */}
            <div className="flex items-center space-x-1 bg-gray-800/50 backdrop-blur-sm rounded-lg p-1">
              <button
                onClick={() => handleZoom('in')}
                className="p-2 hover:bg-gray-700 rounded transition-colors"
              >
                <MagnifyingGlassPlusIcon className="w-5 h-5 text-gray-300" />
              </button>
              <button
                onClick={() => handleZoom('out')}
                className="p-2 hover:bg-gray-700 rounded transition-colors"
              >
                <MagnifyingGlassMinusIcon className="w-5 h-5 text-gray-300" />
              </button>
              <button
                onClick={() => handleZoom('reset')}
                className="p-2 hover:bg-gray-700 rounded transition-colors"
              >
                <ArrowPathIcon className="w-5 h-5 text-gray-300" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Graph */}
      {loading ? (
        <div className="flex items-center justify-center h-full">
          <Loading message="Loading knowledge graph..." />
        </div>
      ) : (
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="bg-gray-900/50"
        />
      )}

      {/* Filter Panel */}
      <motion.div
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        className="absolute left-0 top-20 bottom-0 w-64 bg-gray-900/95 backdrop-blur-sm border-r border-gray-700 p-4 overflow-y-auto"
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <FunnelIcon className="w-5 h-5 mr-2" />
          Filters
        </h3>

        {/* Node Type Filters */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Node Types</h4>
          {Object.keys(nodeTypeColors).map(type => (
            <label key={type} className="flex items-center space-x-2 mb-2">
              <input
                type="checkbox"
                checked={filterOptions.nodeTypes.includes(type)}
                onChange={() => toggleFilter('nodeTypes', type)}
                className="rounded border-gray-600 bg-gray-800 text-blue-500"
              />
              <span className="text-sm text-gray-300 capitalize">{type}</span>
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: nodeTypeColors[type] }}
              />
            </label>
          ))}
        </div>

        {/* Connection Type Filters */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Connection Types</h4>
          {Object.keys(connectionTypeStyles).map(type => (
            <label key={type} className="flex items-center space-x-2 mb-2">
              <input
                type="checkbox"
                checked={filterOptions.connectionTypes.includes(type)}
                onChange={() => toggleFilter('connectionTypes', type)}
                className="rounded border-gray-600 bg-gray-800 text-blue-500"
              />
              <span className="text-sm text-gray-300 capitalize">
                {type.replace('_', ' ')}
              </span>
            </label>
          ))}
        </div>

        {/* Degree Filter */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-400 mb-2">
            Minimum Connections: {filterOptions.minDegree}
          </h4>
          <input
            type="range"
            min="0"
            max="10"
            value={filterOptions.minDegree}
            onChange={(e) => setFilterOptions(prev => ({
              ...prev,
              minDegree: parseInt(e.target.value)
            }))}
            className="w-full"
          />
        </div>
      </motion.div>

      {/* Node Details Panel */}
      <AnimatePresence>
        {(selectedNode || hoveredNode) && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className="absolute right-0 top-20 w-80 bg-gray-900/95 backdrop-blur-sm border-l border-gray-700 p-4"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">
                {selectedNode ? 'Node Details' : 'Quick View'}
              </h3>
              {selectedNode && (
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-gray-400 hover:text-white"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              )}
            </div>

            {(selectedNode || hoveredNode) && (
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-400">Title</h4>
                  <p className="text-white mt-1">
                    {(selectedNode || hoveredNode).label}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-400">Type</h4>
                  <div className="flex items-center mt-1">
                    <div
                      className="w-3 h-3 rounded-full mr-2"
                      style={{
                        backgroundColor: nodeTypeColors[(selectedNode || hoveredNode).type]
                      }}
                    />
                    <span className="text-white capitalize">
                      {(selectedNode || hoveredNode).type}
                    </span>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-400">Connections</h4>
                  <p className="text-white mt-1">
                    {(selectedNode || hoveredNode).degree} connections
                  </p>
                </div>

                {(selectedNode || hoveredNode).attributes?.keywords?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-400">Keywords</h4>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {(selectedNode || hoveredNode).attributes.keywords.map(keyword => (
                        <span
                          key={keyword}
                          className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedNode && (
                  <button
                    onClick={() => onNodeSelect && onNodeSelect(selectedNode)}
                    className="w-full mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    View Document
                  </button>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search Results */}
      <AnimatePresence>
        {searchResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-4 left-4 right-4 bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-lg p-4 max-h-48 overflow-y-auto"
          >
            <h3 className="text-sm font-medium text-gray-400 mb-2">
              Search Results ({searchResults.length})
            </h3>
            <div className="space-y-2">
              {searchResults.map(result => (
                <div
                  key={result.node_id}
                  className="flex items-center justify-between p-2 hover:bg-gray-800 rounded cursor-pointer"
                  onClick={() => {
                    // Focus on node
                    const node = graphData.nodes.find(n => n.id === result.node_id);
                    if (node) {
                      handleNodeClick(null, node);
                    }
                  }}
                >
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: nodeTypeColors[result.type] }}
                    />
                    <span className="text-sm text-white">{result.title}</span>
                  </div>
                  <span className="text-xs text-gray-400">
                    Score: {result.score}
                  </span>
                </div>
              ))}
            </div>
            <button
              onClick={() => setSearchResults([])}
              className="mt-2 text-xs text-gray-400 hover:text-white"
            >
              Clear results
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Trending Topics */}
      {trends && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute bottom-4 right-4 bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-lg p-4"
        >
          <h3 className="text-sm font-medium text-gray-400 mb-2 flex items-center">
            <TrendingUpIcon className="w-4 h-4 mr-1" />
            Trending Topics
          </h3>
          <div className="space-y-1">
            {trends.trending_keywords.slice(0, 5).map(([keyword, count]) => (
              <div key={keyword} className="text-xs text-gray-300">
                {keyword} ({count})
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default KnowledgeGraphExplorer;