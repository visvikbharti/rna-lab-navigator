import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { Card } from './enhanced/Card';
import { Button } from './enhanced/Button';
import { Input } from './enhanced/Input';
import useWebSocket from '../hooks/useWebSocket';
import './KnowledgeGraph.css';

const KnowledgeGraph = () => {
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], clusters: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [filters, setFilters] = useState({
    nodeTypes: [],
    edgeTypes: [],
    searchQuery: ''
  });
  const [loading, setLoading] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  
  // WebSocket connection
  const { sendMessage, lastMessage } = useWebSocket('/ws/knowledge-graph/');
  
  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const container = svgRef.current?.parentElement;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: container.clientHeight || 600
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      
      switch (data.type) {
        case 'initial_data':
        case 'graph_data':
          setGraphData(data.data);
          setLoading(false);
          break;
          
        case 'update':
          handleGraphUpdate(data.data);
          break;
          
        case 'node_details':
          setSelectedNode(data.data);
          break;
          
        case 'error':
          console.error('WebSocket error:', data.message);
          break;
      }
    }
  }, [lastMessage]);
  
  // Handle real-time updates
  const handleGraphUpdate = (update) => {
    const { type, metadata } = update;
    
    // Show notification
    showNotification(`New ${type.replace('_', ' ')}: ${getUpdateDescription(metadata)}`);
    
    // Request updated graph data
    requestGraphData();
  };
  
  const getUpdateDescription = (metadata) => {
    if (metadata.node) {
      return metadata.node.label;
    } else if (metadata.edge) {
      return `${metadata.edge.source} → ${metadata.edge.target}`;
    } else if (metadata.cluster) {
      return metadata.cluster.name;
    }
    return '';
  };
  
  const showNotification = (message) => {
    // Create and show notification toast
    const notification = document.createElement('div');
    notification.className = 'graph-notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('fade-out');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  };
  
  // Request graph data with filters
  const requestGraphData = useCallback(() => {
    sendMessage({
      type: 'get_graph',
      filters: {
        node_types: filters.nodeTypes.length > 0 ? filters.nodeTypes : null,
        edge_types: filters.edgeTypes.length > 0 ? filters.edgeTypes : null
      }
    });
  }, [filters, sendMessage]);
  
  // Initialize and update D3 visualization
  useEffect(() => {
    if (!graphData.nodes.length) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    
    const { width, height } = dimensions;
    
    // Create container groups
    const g = svg.append('g');
    
    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    
    svg.call(zoom);
    
    // Color scale for node types
    const colorScale = d3.scaleOrdinal()
      .domain(['document', 'concept', 'author', 'method', 'finding', 'protocol'])
      .range(['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']);
    
    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force('link', d3.forceLink(graphData.edges)
        .id(d => d.index)
        .distance(d => 100 / (d.weight || 1)))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));
    
    // Draw clusters
    const clusters = g.append('g')
      .attr('class', 'clusters')
      .selectAll('g')
      .data(graphData.clusters)
      .enter().append('g')
      .attr('class', 'cluster');
    
    // Draw cluster hulls (will be updated in tick)
    clusters.append('path')
      .attr('class', 'cluster-hull')
      .style('fill', (d, i) => d3.schemeSet3[i % 12])
      .style('opacity', 0.1)
      .style('stroke', (d, i) => d3.schemeSet3[i % 12])
      .style('stroke-width', 2)
      .style('stroke-opacity', 0.3);
    
    // Draw edges
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graphData.edges)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', d => 0.3 + (d.weight || 0.5) * 0.4)
      .attr('stroke-width', d => 1 + (d.weight || 0.5) * 2)
      .attr('class', d => `edge edge-${d.type}`);
    
    // Draw nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graphData.nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));
    
    // Add circles for nodes
    node.append('circle')
      .attr('r', d => {
        const baseSize = 8;
        const connections = graphData.edges.filter(
          e => e.source === d.index || e.target === d.index
        ).length;
        return baseSize + Math.sqrt(connections) * 2;
      })
      .attr('fill', d => colorScale(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);
    
    // Add labels
    node.append('text')
      .text(d => d.label)
      .attr('x', 0)
      .attr('y', -12)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .style('pointer-events', 'none');
    
    // Add hover effects
    node.on('mouseenter', function(event, d) {
      // Highlight connected nodes and edges
      const connectedNodes = new Set();
      const connectedEdges = new Set();
      
      graphData.edges.forEach(edge => {
        if (edge.source === d.index) {
          connectedNodes.add(edge.target);
          connectedEdges.add(edge);
        } else if (edge.target === d.index) {
          connectedNodes.add(edge.source);
          connectedEdges.add(edge);
        }
      });
      
      // Dim non-connected elements
      node.style('opacity', n => 
        n.index === d.index || connectedNodes.has(n.index) ? 1 : 0.3
      );
      
      link.style('opacity', e => connectedEdges.has(e) ? 1 : 0.1);
      
      // Show tooltip
      showTooltip(event, d);
    })
    .on('mouseleave', function() {
      // Reset opacity
      node.style('opacity', 1);
      link.style('opacity', d => 0.3 + (d.weight || 0.5) * 0.4);
      
      // Hide tooltip
      hideTooltip();
    })
    .on('click', function(event, d) {
      // Request detailed node information
      sendMessage({
        type: 'get_node_details',
        node_id: d.id
      });
    });
    
    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => graphData.nodes[d.source].x)
        .attr('y1', d => graphData.nodes[d.source].y)
        .attr('x2', d => graphData.nodes[d.target].x)
        .attr('y2', d => graphData.nodes[d.target].y);
      
      node.attr('transform', d => `translate(${d.x},${d.y})`);
      
      // Update cluster hulls
      clusters.select('.cluster-hull')
        .attr('d', d => {
          const points = d.nodes.map(nodeIdx => [
            graphData.nodes[nodeIdx].x,
            graphData.nodes[nodeIdx].y
          ]);
          
          if (points.length < 3) return null;
          
          return d3.line()
            .curve(d3.curveCardinalClosed.tension(0.8))(
              d3.polygonHull(points)
            );
        });
    });
    
    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [graphData, dimensions]);
  
  // Tooltip functions
  const showTooltip = (event, d) => {
    const tooltip = d3.select(tooltipRef.current);
    
    tooltip
      .style('opacity', 1)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 10}px`)
      .html(`
        <strong>${d.label}</strong><br/>
        Type: ${d.type}<br/>
        ${d.properties.year ? `Year: ${d.properties.year}<br/>` : ''}
        ${d.properties.authors ? `Authors: ${d.properties.authors}<br/>` : ''}
      `);
  };
  
  const hideTooltip = () => {
    d3.select(tooltipRef.current).style('opacity', 0);
  };
  
  // Filter handlers
  const handleNodeTypeFilter = (type) => {
    setFilters(prev => ({
      ...prev,
      nodeTypes: prev.nodeTypes.includes(type)
        ? prev.nodeTypes.filter(t => t !== type)
        : [...prev.nodeTypes, type]
    }));
  };
  
  const handleEdgeTypeFilter = (type) => {
    setFilters(prev => ({
      ...prev,
      edgeTypes: prev.edgeTypes.includes(type)
        ? prev.edgeTypes.filter(t => t !== type)
        : [...prev.edgeTypes, type]
    }));
  };
  
  // Apply filters
  useEffect(() => {
    requestGraphData();
  }, [filters.nodeTypes, filters.edgeTypes]);
  
  // Actions
  const handleDiscoverConnections = () => {
    sendMessage({ type: 'discover_connections' });
  };
  
  const handleTriggerClustering = () => {
    sendMessage({ type: 'request_clustering' });
  };
  
  const handleSearch = (e) => {
    e.preventDefault();
    // Implement search functionality
  };
  
  return (
    <div className="knowledge-graph-container">
      <Card className="graph-controls">
        <div className="controls-row">
          <div className="filter-section">
            <h4>Node Types</h4>
            <div className="filter-chips">
              {['document', 'concept', 'author', 'method', 'finding', 'protocol'].map(type => (
                <button
                  key={type}
                  className={`filter-chip ${filters.nodeTypes.includes(type) ? 'active' : ''}`}
                  onClick={() => handleNodeTypeFilter(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          
          <div className="filter-section">
            <h4>Edge Types</h4>
            <div className="filter-chips">
              {['cites', 'uses', 'supports', 'extends', 'related_to'].map(type => (
                <button
                  key={type}
                  className={`filter-chip ${filters.edgeTypes.includes(type) ? 'active' : ''}`}
                  onClick={() => handleEdgeTypeFilter(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          
          <div className="action-buttons">
            <Button onClick={handleDiscoverConnections} variant="secondary">
              Discover Connections
            </Button>
            <Button onClick={handleTriggerClustering} variant="secondary">
              Cluster Nodes
            </Button>
          </div>
        </div>
        
        <form onSubmit={handleSearch} className="search-form">
          <Input
            type="text"
            placeholder="Search nodes..."
            value={filters.searchQuery}
            onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
          />
          <Button type="submit">Search</Button>
        </form>
      </Card>
      
      <div className="graph-wrapper">
        {loading ? (
          <div className="loading-spinner">Loading graph...</div>
        ) : (
          <>
            <svg
              ref={svgRef}
              width={dimensions.width}
              height={dimensions.height}
              className="knowledge-graph-svg"
            />
            <div ref={tooltipRef} className="graph-tooltip" />
          </>
        )}
      </div>
      
      {selectedNode && (
        <Card className="node-details-panel">
          <h3>{selectedNode.node.label}</h3>
          <div className="node-info">
            <p><strong>Type:</strong> {selectedNode.node.type}</p>
            <p><strong>Created:</strong> {new Date(selectedNode.node.created_at).toLocaleDateString()}</p>
            
            {selectedNode.node.document && (
              <p><strong>Document:</strong> {selectedNode.node.document.title}</p>
            )}
            
            {Object.entries(selectedNode.node.properties).map(([key, value]) => (
              <p key={key}><strong>{key}:</strong> {value}</p>
            ))}
          </div>
          
          <div className="connections">
            <h4>Connections</h4>
            
            {selectedNode.connections.outgoing.length > 0 && (
              <div className="connection-list">
                <h5>Outgoing</h5>
                {selectedNode.connections.outgoing.map((edge, idx) => (
                  <div key={idx} className="connection-item">
                    <span className="edge-type">{edge.type}</span>
                    <span className="target">{edge.target}</span>
                  </div>
                ))}
              </div>
            )}
            
            {selectedNode.connections.incoming.length > 0 && (
              <div className="connection-list">
                <h5>Incoming</h5>
                {selectedNode.connections.incoming.map((edge, idx) => (
                  <div key={idx} className="connection-item">
                    <span className="source">{edge.source}</span>
                    <span className="edge-type">{edge.type}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <Button onClick={() => setSelectedNode(null)} variant="secondary">
            Close
          </Button>
        </Card>
      )}
    </div>
  );
};

export default KnowledgeGraph;