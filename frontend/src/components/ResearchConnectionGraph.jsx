import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import * as d3 from 'd3';
import { getResearchConnections } from '../api/intelligence';
import Loading from './enhanced/Loading';

const connectionColors = {
  complementary_methods: '#3B82F6', // blue
  contradictory_findings: '#EF4444', // red
  method_transfer: '#8B5CF6', // purple
  missing_citation: '#F59E0B', // yellow
  converging_trend: '#10B981' // green
};

function ResearchConnectionGraph({ papers, insights, onNodeClick }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);

  useEffect(() => {
    loadGraphData();
  }, [papers, insights]);

  useEffect(() => {
    if (graphData) {
      drawGraph();
    }
  }, [graphData, dimensions]);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: Math.min(600, width * 0.75) });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadGraphData = async () => {
    setLoading(true);
    
    try {
      if (insights && insights.length > 0) {
        // Build graph from insights
        const nodes = new Map();
        const edges = [];

        // Add papers as nodes
        insights.forEach(insight => {
          insight.papers_involved.forEach(paperId => {
            if (!nodes.has(paperId)) {
              const paper = papers?.find(p => p.doc_id === paperId);
              nodes.set(paperId, {
                id: paperId,
                title: paper?.title || `Paper ${paperId}`,
                year: paper?.metadata?.year || 'Unknown',
                nodeType: 'paper'
              });
            }
          });

          // Add edges for each insight
          if (insight.papers_involved.length >= 2) {
            for (let i = 0; i < insight.papers_involved.length - 1; i++) {
              for (let j = i + 1; j < insight.papers_involved.length; j++) {
                edges.push({
                  source: insight.papers_involved[i],
                  target: insight.papers_involved[j],
                  connection_type: insight.insight_type,
                  strength: insight.confidence_score,
                  description: insight.title
                });
              }
            }
          }
        });

        setGraphData({
          nodes: Array.from(nodes.values()),
          edges
        });
      } else if (papers && papers.length > 0) {
        // Fetch connections from API
        const response = await getResearchConnections({
          paper_ids: papers.map(p => p.doc_id).join(',')
        });
        setGraphData(response);
      }
    } catch (error) {
      console.error('Error loading graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  const drawGraph = () => {
    if (!graphData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;
    const g = svg.append('g');

    // Create zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force('link', d3.forceLink(graphData.edges)
        .id(d => d.id)
        .distance(d => 150 * (1 - d.strength))
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Create arrow markers for directed edges
    const defs = svg.append('defs');
    Object.entries(connectionColors).forEach(([type, color]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color);
    });

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(graphData.edges)
      .enter().append('line')
      .attr('stroke', d => connectionColors[d.connection_type] || '#999')
      .attr('stroke-opacity', d => 0.3 + d.strength * 0.7)
      .attr('stroke-width', d => 1 + d.strength * 3)
      .attr('marker-end', d => `url(#arrow-${d.connection_type})`);

    // Create nodes
    const node = g.append('g')
      .selectAll('g')
      .data(graphData.nodes)
      .enter().append('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add circles for nodes
    node.append('circle')
      .attr('r', 20)
      .attr('fill', d => d.nodeType === 'paper' ? '#4F46E5' : '#10B981')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add labels
    node.append('text')
      .text(d => d.title.length > 30 ? d.title.substring(0, 30) + '...' : d.title)
      .attr('x', 0)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#374151');

    // Add year labels
    node.append('text')
      .text(d => d.year)
      .attr('x', 0)
      .attr('y', 45)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#6B7280');

    // Add tooltips
    const tooltip = d3.select('body').append('div')
      .attr('class', 'graph-tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px 12px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none');

    // Node interactions
    node
      .on('click', (event, d) => {
        setSelectedNode(d);
        if (onNodeClick) {
          onNodeClick(d.id);
        }
      })
      .on('mouseover', (event, d) => {
        setHoveredNode(d);
        tooltip.transition().duration(200).style('opacity', 0.9);
        tooltip.html(`
          <strong>${d.title}</strong><br/>
          Year: ${d.year}<br/>
          Connections: ${graphData.edges.filter(e => 
            e.source.id === d.id || e.target.id === d.id
          ).length}
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', () => {
        setHoveredNode(null);
        tooltip.transition().duration(200).style('opacity', 0);
      });

    // Link interactions
    link
      .on('mouseover', (event, d) => {
        tooltip.transition().duration(200).style('opacity', 0.9);
        tooltip.html(`
          <strong>${d.description}</strong><br/>
          Type: ${d.connection_type.replace(/_/g, ' ')}<br/>
          Strength: ${(d.strength * 100).toFixed(0)}%
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', () => {
        tooltip.transition().duration(200).style('opacity', 0);
      });

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
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

    // Cleanup tooltip on unmount
    return () => {
      d3.select('body').selectAll('.graph-tooltip').remove();
    };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Loading message="Building connection graph..." />
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Research Connection Network
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Visualizing relationships between papers based on discovered insights
        </p>
      </div>

      <div ref={containerRef} className="relative">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="w-full"
        />
        
        {/* Legend */}
        <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-md p-3 space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Connection Types
          </h4>
          {Object.entries(connectionColors).map(([type, color]) => (
            <div key={type} className="flex items-center space-x-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {type.replace(/_/g, ' ')}
              </span>
            </div>
          ))}
        </div>

        {/* Selected Node Info */}
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-4 left-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4"
          >
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">
              {selectedNode.title}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Year: {selectedNode.year}
            </p>
            <button
              onClick={() => setSelectedNode(null)}
              className="mt-2 text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Close
            </button>
          </motion.div>
        )}
      </div>

      {/* Stats */}
      {graphData && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {graphData.nodes.length}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Papers</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {graphData.edges.length}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Connections</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {new Set(graphData.edges.map(e => e.connection_type)).size}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Insight Types</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResearchConnectionGraph;