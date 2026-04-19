import React, { useEffect, useRef, useState, useMemo } from 'react';
import { X, ZoomIn, ZoomOut, RotateCw, Download, Maximize2, Minimize2, Info } from 'lucide-react';

// Dynamic import for cytoscape - will be loaded when component mounts
let cytoscape = null;
let dagreAvailable = false;
let cytoscapeLoading = false;
let cytoscapePromise = null;

// Load cytoscape dynamically
const loadCytoscape = async () => {
  if (cytoscape) return cytoscape;
  if (cytoscapeLoading && cytoscapePromise) return cytoscapePromise;
  
  cytoscapeLoading = true;
  cytoscapePromise = (async () => {
    try {
      const cytoscapeModule = await import('cytoscape');
      cytoscape = cytoscapeModule.default || cytoscapeModule;
      
      // Try to load dagre
      try {
        const dagreModule = await import('cytoscape-dagre');
        const dagre = dagreModule.default || dagreModule;
        if (dagre && cytoscape) {
          cytoscape.use(dagre);
          dagreAvailable = true;
        }
      } catch (e) {
        console.warn('cytoscape-dagre not available:', e.message);
      }
      
      cytoscapeLoading = false;
      return cytoscape;
    } catch (e) {
      console.error('Failed to load cytoscape:', e);
      cytoscapeLoading = false;
      return null;
    }
  })();
  
  return cytoscapePromise;
};

const CitationMesh = ({ papers, onClose, onNodeClick }) => {
  const [elements, setElements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [layout, setLayout] = useState('concentric'); // Default to circular/clustered layout
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showOnlyRootNodes, setShowOnlyRootNodes] = useState(false);
  const [minCitations, setMinCitations] = useState(0);
  const [showLabels, setShowLabels] = useState(true);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: null });
  const cyRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    // Load cytoscape first, then build network
    loadCytoscape().then((cy) => {
      if (!cy) {
        setError('Cytoscape library not installed. Please stop the server and run: npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save');
        setLoading(false);
        return;
      }

      if (!papers || papers.length === 0) {
        setError('No papers available to build citation network');
        setLoading(false);
        return;
      }

      buildNetwork();
    }).catch((err) => {
      console.error('Error loading cytoscape:', err);
      setError('Failed to load cytoscape library. Please install: npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save');
      setLoading(false);
    });
  }, [papers]);

  useEffect(() => {
    // Destroy existing graph before creating new one
    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    // Initialize cytoscape when container is ready and elements are loaded
    if (containerRef.current && elements.length > 0) {
      loadCytoscape().then((cy) => {
        if (cy && containerRef.current && elements.length > 0) {
          initializeCytoscape(cy);
        }
      });
    }

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [elements, layout, showLabels]);

  const initializeCytoscape = (cyLib) => {
    if (!cyLib || !containerRef.current) {
      console.error('Cytoscape not available');
      setError('Cytoscape library not available. Please run: npm install cytoscape');
      return;
    }

    try {
      const cy = cyLib({
        container: containerRef.current,
        elements: elements,
        style: getStylesheet(), // Use dynamic stylesheet
        layout: getLayoutConfig(layout),
        minZoom: 0.05, // Allow zooming out much more
        maxZoom: 4, // Allow zooming in more
        wheelSensitivity: 0.15, // Slower zoom with mouse wheel for better control
      });

      // Add hover effects with tooltip
      cy.on('mouseover', 'node', (evt) => {
        const node = evt.target;
        const nodeData = node.data();
        const position = node.renderedPosition();
        
        // Show enhanced tooltip
        const authors = nodeData.authors && nodeData.authors.length > 0
          ? nodeData.authors.slice(0, 3).join(', ') + (nodeData.authors.length > 3 ? ' et al.' : '')
          : 'Unknown authors';
        
        setTooltip({
          visible: true,
          x: position.x,
          y: position.y - 60,
          content: {
            title: nodeData.title,
            year: nodeData.year || 'N/A',
            citations: nodeData.citationCount || 0,
            authors: authors,
            venue: nodeData.venue || 'N/A',
            isRoot: nodeData.isRoot,
            influenceScore: nodeData.influenceScore || 0,
            pageRankScore: nodeData.pageRankScore || 0,
            citationVelocity: nodeData.citationVelocity || 0
          }
        });
        
        node.style('overlay-opacity', 0.3);
        node.style('z-index', 999);
      });

      cy.on('mouseout', 'node', (evt) => {
        const node = evt.target;
        setTooltip({ visible: false, x: 0, y: 0, content: null });
        node.style('overlay-opacity', 0);
        node.style('z-index', 'auto');
      });

      cy.on('tap', 'node', handleNodeClick);
      
      // Pan and zoom controls
      cy.boxSelectionEnabled(false);
      cy.userPanningEnabled(true);
      cy.userZoomingEnabled(true);
      
      // Fit with padding for better view
      cy.fit(undefined, 80); // More padding for less congestion
      
      // Set initial zoom to see more of the graph - zoom out significantly
      setTimeout(() => {
        const currentZoom = cy.zoom();
        if (currentZoom > 0.5) {
          cy.zoom(0.4); // Zoom out significantly to reduce congestion
          cy.center();
        }
        
        // Debug: Log edge count
        const edgeCount = cy.edges().length;
        const nodeCount = cy.nodes().length;
        console.log('Cytoscape initialized:', { nodes: nodeCount, edges: edgeCount });
        if (edgeCount === 0 && nodeCount > 0) {
          console.warn('No edges found! Check edge data:', cy.elements());
        }
      }, 100);
      
      cyRef.current = cy;
    } catch (err) {
      console.error('Error initializing cytoscape:', err);
      setError('Failed to initialize graph visualization: ' + err.message);
    }
  };

  const buildNetwork = async () => {
    setLoading(true);
    setError(null);

    try {
      // Import API service
      const { searchAPI } = await import('../services/api');
      
      // Build citation network (optimized for speed and reliability)
      const response = await searchAPI.getCitationNetwork(papers, 1, 50); // Balanced network building
      
      if (response.status === 'success' && response.network) {
        let { nodes, edges } = response.network;
        
        // Filter nodes if needed
        if (showOnlyRootNodes) {
          nodes = nodes.filter(n => n.isRoot);
          const rootIds = new Set(nodes.map(n => String(n.id)));
          edges = edges.filter(e => rootIds.has(String(e.source)) && rootIds.has(String(e.target)));
        }
        
        // Filter by minimum citations
        if (minCitations > 0) {
          nodes = nodes.filter(n => (n.citationCount || 0) >= minCitations);
          const nodeIds = new Set(nodes.map(n => String(n.id)));
          edges = edges.filter(e => nodeIds.has(String(e.source)) && nodeIds.has(String(e.target)));
        }
        
        console.log('After filtering:', { nodes: nodes.length, edges: edges.length });
        
        // Convert to Cytoscape format with clean, minimal labels
        const cyNodes = nodes.map((node) => {
          const title = node.title || node.label || 'Untitled';
          
          // Shorter truncation for cleaner look
          const maxLength = node.isRoot ? 60 : 45;
          const truncatedTitle = title.length > maxLength 
            ? title.substring(0, maxLength) + '...' 
            : title;
          
          return {
            data: {
              id: String(node.id),
              label: truncatedTitle, // Clean, simple title only
              title: title,
              year: node.year,
              citationCount: node.citationCount || 0,
              authors: node.authors || [],
              venue: node.venue,
              isRoot: node.isRoot || false,
              influenceScore: node.influenceScore || 0,
              pageRankScore: node.pageRankScore || 0,
              citationVelocity: node.citationVelocity || 0,
            },
            classes: node.isRoot ? 'root-node' : 'citation-node',
          };
        });

        const cyEdges = edges.map((edge) => ({
          data: {
            id: `${edge.source}-${edge.target}`,
            source: String(edge.source), // Ensure string IDs
            target: String(edge.target), // Ensure string IDs
            type: edge.type || 'cites',
          },
        }));

        console.log('Network built:', {
          nodes: cyNodes.length,
          edges: cyEdges.length,
          sampleEdge: cyEdges[0],
          sampleNode: cyNodes[0],
          allNodeIds: cyNodes.map(n => n.data.id).slice(0, 5),
          allEdgeSources: cyEdges.map(e => e.data.source).slice(0, 5),
          allEdgeTargets: cyEdges.map(e => e.data.target).slice(0, 5)
        });
        
        if (cyEdges.length === 0 && cyNodes.length > 1) {
          console.warn('No edges found! This might mean papers don\'t reference each other in the dataset.');
        }

        setElements([...cyNodes, ...cyEdges]);
      } else {
        setError('Failed to build citation network');
      }
    } catch (err) {
      console.error('Error building citation network:', err);
      setError(err.message || 'Failed to build citation network');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (evt) => {
    const node = evt.target;
    if (node.isNode() && onNodeClick) {
      const nodeData = node.data();
      onNodeClick({
        paperId: nodeData.id,
        title: nodeData.title,
        year: nodeData.year,
        citationCount: nodeData.citationCount,
        authors: nodeData.authors,
        venue: nodeData.venue,
      });
    }
  };

  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8);
    }
  };

  const handleReset = () => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 80); // More padding
      cyRef.current.center();
      // Zoom out a bit more for better view
      setTimeout(() => {
        if (cyRef.current.zoom() > 0.5) {
          cyRef.current.zoom(0.4);
        }
      }, 100);
    }
  };

  const handleLayoutChange = (newLayout) => {
    setLayout(newLayout);
    if (cyRef.current && elements.length > 0) {
      // Apply new layout to existing graph
      const layoutConfig = getLayoutConfig(newLayout);
      cyRef.current.layout(layoutConfig).run();
    }
  };

  const handleToggleLabels = () => {
    setShowLabels(prev => !prev);
  };

  const handleExport = () => {
    if (cyRef.current) {
      const png = cyRef.current.png({ full: true, bg: 'white' });
      const link = document.createElement('a');
      link.download = 'citation-network.png';
      link.href = png;
      link.click();
    }
  };

  const getLayoutConfig = (layoutName) => {
    const configs = {
      concentric: {
        name: 'concentric',
        fit: true,
        padding: 80,
        startAngle: 0,
        sweep: 360,
        clockwise: true,
        equidistant: false,
        minNodeSpacing: 180, // Increased spacing for better readability
        height: undefined,
        width: undefined,
        spacing: 200, // More space between concentric levels
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: true,
        animate: true,
        animationDuration: 600,
        animationEasing: 'ease-out',
      },
      circle: {
        name: 'circle',
        fit: true,
        padding: 80,
        startAngle: 0,
        sweep: 360,
        clockwise: true,
        radius: undefined,
        spacing: 200, // More space between nodes
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: true,
        animate: true,
        animationDuration: 600,
        animationEasing: 'ease-out',
      },
      breadthfirst: {
        name: 'breadthfirst',
        directed: true,
        spacingFactor: 3.5, // Increased for better spacing
        fit: true,
        padding: 80,
        animate: true,
        animationDuration: 600,
        animationEasing: 'ease-out',
        grid: false,
      },
      cose: {
        name: 'cose',
        quality: 'default',
        nodeRepulsion: 15000, // Increased repulsion for more space
        idealEdgeLength: 250, // Longer edges for cleaner layout
        edgeElasticity: 200,
        fit: true,
        padding: 80,
        animate: true,
        animationDuration: 600,
        randomize: true,
        componentSpacing: 150,
        nodeOverlap: 20,
      },
    };

    if (dagreAvailable && layoutName === 'dagre') {
      return {
        name: 'dagre',
        rankDir: 'TB',
        spacingFactor: 2.5, // Increased spacing
        nodeSep: 200, // More space between nodes
        edgeSep: 80,
        rankSep: 250, // More space between ranks
        fit: true,
        padding: 80,
        animate: true,
        animationDuration: 600,
        animationEasing: 'ease-out',
      };
    }

    return configs[layoutName] || configs.concentric;
  };

  const getStylesheet = () => {
    const labelValue = showLabels ? 'data(label)' : '';
    return [
    {
      selector: 'node',
      style: {
        'background-color': '#F8FAFC',
        'label': labelValue,
        'width': 60,
        'height': 60,
        'text-valign': 'bottom',
        'text-halign': 'center',
        'color': '#1E293B',
        'font-size': '11px',
        'font-weight': '500',
        'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        'text-wrap': 'wrap',
        'text-max-width': '140px',
        'text-overflow-wrap': 'anywhere',
        'text-margin-y': '8px',
        'border-width': 2,
        'border-color': '#CBD5E1',
        'shape': 'ellipse',
        'text-background-color': '#FFFFFF',
        'text-background-opacity': 0.95,
        'text-background-padding': '4px 8px',
        'text-background-shape': 'roundrectangle',
        'background-opacity': 1,
        'transition-property': 'background-color, border-color, border-width',
        'transition-duration': '0.2s',
      },
    },
    {
      selector: 'node.root-node',
      style: {
        'background-color': 'mapData(pageRankScore, 0, 1, #93C5FD, #1E3A8A)',
        'label': labelValue,
        'width': 'mapData(influenceScore, 0, 1, 70, 110)',
        'height': 'mapData(influenceScore, 0, 1, 70, 110)',
        'border-width': 3,
        'border-color': '#2563EB',
        'font-weight': '600',
        'font-size': '12px',
        'color': '#1E293B',
        'text-background-color': '#FFFFFF',
        'text-background-opacity': 0.98,
        'text-background-padding': '6px 10px',
        'z-index': 100,
      },
    },
    {
      selector: 'node.citation-node',
      style: {
        'background-color': 'mapData(pageRankScore, 0, 1, #E2E8F0, #475569)',
        'label': labelValue,
        'width': 'mapData(influenceScore, 0, 1, 45, 85)',
        'height': 'mapData(influenceScore, 0, 1, 45, 85)',
        'font-size': '10px',
        'font-weight': '500',
        'border-color': '#94A3B8',
        'border-width': 2,
        'color': '#475569',
      },
    },
    {
      selector: 'edge',
      style: {
        'width': 1.5,
        'line-color': '#CBD5E1',
        'target-arrow-color': '#94A3B8',
        'target-arrow-shape': 'triangle',
        'target-arrow-size': 6,
        'curve-style': 'bezier',
        'opacity': 0.5,
        'line-style': 'solid',
        'transition-property': 'line-color, width, opacity',
        'transition-duration': '0.2s',
      },
    },
    {
      selector: 'node:selected',
      style: {
        'background-color': '#3B82F6',
        'border-color': '#2563EB',
        'border-width': 4,
        'z-index': 999,
      },
    },
    {
      selector: 'node:hover',
      style: {
        'background-color': '#60A5FA',
        'border-color': '#3B82F6',
        'border-width': 3,
        'z-index': 500,
      },
    },
    {
      selector: 'edge:hover',
      style: {
        'width': 2.5,
        'line-color': '#64748B',
        'target-arrow-color': '#475569',
        'opacity': 0.8,
      },
    },
  ];
  };

  const layoutOptions = useMemo(() => {
    const options = {
      concentric: 'Concentric (Circular Clusters)',
      circle: 'Circle',
      cose: 'Force-Directed',
      breadthfirst: 'Breadthfirst',
    };

    if (dagreAvailable) {
      options.dagre = 'Dagre (Hierarchical)';
    }

    return options;
  }, []);

  // Set default layout if dagre is not available
  useEffect(() => {
    if (layout === 'dagre' && !dagreAvailable) {
      setLayout('concentric');
    }
  }, [layout]);

  // Cytoscape should always be available if imported correctly

  return (
    <div className={`fixed inset-0 bg-white z-50 ${isFullscreen ? '' : 'md:inset-y-4 md:inset-x-4 md:rounded-lg'} shadow-2xl flex flex-col`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-black">Citation Network</h2>
          {loading && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-black"></div>
              <span>Building network...</span>
            </div>
          )}
          {elements.length > 0 && (
            <span className="text-sm text-gray-600">
              {elements.filter(e => e.data && e.data.id && !e.data.source).length} nodes,{' '}
              {elements.filter(e => e.data && e.data.source).length} edges
              {elements.filter(e => e.data && e.data.source).length === 0 && elements.filter(e => e.data && e.data.id && !e.data.source).length > 1 && (
                <span className="text-amber-600 ml-2">(No connections found)</span>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
          </button>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-slate-50 flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={layout}
            onChange={(e) => handleLayoutChange(e.target.value)}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white"
          >
            {Object.entries(layoutOptions).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showOnlyRootNodes}
              onChange={(e) => {
                setShowOnlyRootNodes(e.target.checked);
              }}
              className="rounded border-gray-300 cursor-pointer"
            />
            <span>Root nodes only</span>
          </label>
          
          <div className="flex items-center gap-2 text-sm">
            <label>Min citations:</label>
            <input
              type="number"
              min="0"
              value={minCitations}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 0;
                setMinCitations(val);
              }}
              className="w-16 text-sm border border-gray-300 rounded px-2 py-1"
            />
          </div>
          
          <button
            onClick={() => {
              if (papers && papers.length > 0) {
                buildNetwork();
              }
            }}
            className="px-3 py-1.5 text-sm bg-black text-white rounded hover:bg-gray-800 transition-colors"
          >
            Apply Filters
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
            title="Reset view"
          >
            <RotateCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleExport}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
            title="Export as PNG"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={handleToggleLabels}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-200 transition-colors"
            title={showLabels ? "Hide labels" : "Show labels"}
          >
            {showLabels ? 'Hide Labels' : 'Show Labels'}
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 relative bg-white">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center p-6">
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={buildNetwork}
                className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        )}
        {loading && elements.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-black mx-auto mb-4"></div>
              <p className="text-gray-600">Building citation network...</p>
            </div>
          </div>
        )}
        <div
          ref={containerRef}
          style={{ width: '100%', height: '100%' }}
          className={loading || error ? 'hidden' : ''}
        />
        
        {/* Clean Tooltip */}
        {tooltip.visible && tooltip.content && (
          <div
            className="absolute z-[1000] pointer-events-none"
            style={{
              left: `${tooltip.x}px`,
              top: `${tooltip.y}px`,
              transform: 'translate(-50%, -100%)',
            }}
          >
            <div className="bg-white rounded-md shadow-lg border border-gray-200 p-3 max-w-xs">
              <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium mb-2 ${
                tooltip.content.isRoot 
                  ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                  : 'bg-gray-50 text-gray-700 border border-gray-200'
              }`}>
                {tooltip.content.isRoot ? 'Search Result' : 'Citation'}
              </div>
              <h3 className="font-semibold text-xs text-gray-900 mb-2 line-clamp-2 leading-tight">
                {tooltip.content.title}
              </h3>
              <div className="space-y-1 text-[11px] text-gray-600">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-gray-500">Year</span>
                  <span className="font-medium text-gray-900">{tooltip.content.year}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-gray-500">Citations</span>
                  <span className="font-medium text-gray-900">{tooltip.content.citations}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-gray-500">Influence Score</span>
                  <span className="font-medium text-blue-600">{(tooltip.content.influenceScore || 0).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-gray-500">PageRank</span>
                  <span className="font-medium text-purple-600">{(tooltip.content.pageRankScore || 0).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-gray-500">Velocity</span>
                  <span className="font-medium text-green-600">{tooltip.content.citationVelocity}/yr</span>
                </div>
                <div className="flex items-start gap-2 pt-1 mt-1 border-t border-gray-100">
                  <span className="text-gray-500 w-12 flex-shrink-0">Authors</span>
                  <span className="line-clamp-1 text-gray-900">{tooltip.content.authors}</span>
                </div>
                {tooltip.content.venue && tooltip.content.venue !== 'N/A' && (
                  <div className="flex items-start gap-2">
                    <span className="text-gray-500 w-12 flex-shrink-0">Venue</span>
                    <span className="line-clamp-1 text-gray-900">{tooltip.content.venue}</span>
                  </div>
                )}
              </div>
              <div className="mt-2 pt-2 border-t border-gray-100 text-[10px] text-gray-400">
                Click node for details
              </div>
            </div>
          </div>
        )}
        
        {!loading && !error && elements.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center p-6">
              <p className="text-gray-600 mb-4">No citation connections found</p>
              <p className="text-sm text-gray-500">
                The papers in your search don't have citation relationships in the current dataset.
              </p>
            </div>
          </div>
        )}
        
        {/* Metrics Legend */}
        {!loading && !error && elements.length > 0 && (
          <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm border border-gray-200 rounded-md shadow-md p-3 z-10 w-64 text-xs pointer-events-auto">
            <h4 className="font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-blue-500" /> Graph Intelligence
            </h4>
            <div className="space-y-2.5 text-gray-600">
              <div className="flex items-start gap-1.5">
                <div className="w-2 h-2 rounded-full bg-purple-500 mt-1 flex-shrink-0"></div>
                <div>
                  <span className="font-medium text-gray-900">PageRank:</span> Measures prestige based on citations from other highly-cited papers. Controls <span className="font-medium text-purple-600">node color</span>.
                </div>
              </div>
              <div className="flex items-start gap-1.5">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-1 flex-shrink-0"></div>
                <div>
                  <span className="font-medium text-gray-900">Influence Score:</span> Represents in-degree centrality (citations within this specific graph). Controls <span className="font-medium text-blue-600">node size</span>.
                </div>
              </div>
              <div className="flex items-start gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500 mt-1 flex-shrink-0"></div>
                <div>
                  <span className="font-medium text-gray-900">Velocity:</span> The average number of new citations this paper receives per year.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CitationMesh;
