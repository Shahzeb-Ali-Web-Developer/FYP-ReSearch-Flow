import React, { useEffect, useRef, useState, useMemo } from 'react';
import { X, ZoomIn, ZoomOut, RotateCw, Download, Maximize2, Minimize2 } from 'lucide-react';

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

      // Add hover effects (visual feedback)
      cy.on('mouseover', 'node', (evt) => {
        const node = evt.target;
        node.style('overlay-opacity', 0.3);
        node.style('z-index', 999);
      });

      cy.on('mouseout', 'node', (evt) => {
        const node = evt.target;
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
      
      // Get more nodes to find connections between papers
      const response = await searchAPI.getCitationNetwork(papers, 1, 50); // Increased to get more connections
      
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
        
        // Convert to Cytoscape format with full titles
        const cyNodes = nodes.map((node) => {
          const title = node.title || node.label || 'Untitled';
          
          return {
            data: {
              id: String(node.id), // Ensure string ID for matching with edges
              label: title, // Full title, no truncation
              title: title,
              year: node.year,
              citationCount: node.citationCount || 0,
              authors: node.authors || [],
              venue: node.venue,
              isRoot: node.isRoot || false,
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
        padding: 60,
        startAngle: 0,
        sweep: 360,
        clockwise: true,
        equidistant: false,
        minNodeSpacing: 120, // Space between nodes in same level
        height: undefined,
        width: undefined,
        spacing: 150, // Space between concentric levels
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: true,
        animate: true,
        animationDuration: 800,
      },
      circle: {
        name: 'circle',
        fit: true,
        padding: 60,
        startAngle: 0,
        sweep: 360,
        clockwise: true,
        radius: undefined, // Auto-calculate
        spacing: 150, // Space between nodes
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: true,
        animate: true,
        animationDuration: 800,
      },
      breadthfirst: {
        name: 'breadthfirst',
        directed: true,
        spacingFactor: 3.0,
        fit: true,
        padding: 60,
        animate: true,
        animationDuration: 800,
      },
      cose: {
        name: 'cose',
        quality: 'default',
        nodeRepulsion: 10000,
        idealEdgeLength: 200,
        fit: true,
        padding: 60,
        animate: true,
        animationDuration: 800,
        randomize: true,
      },
    };

    if (dagreAvailable && layoutName === 'dagre') {
      return {
        name: 'dagre',
        rankDir: 'TB', // Top to bottom instead of left to right
        spacingFactor: 2.0,
        nodeSep: 150,
        edgeSep: 50,
        rankSep: 200,
        fit: true,
        padding: 50,
        animate: true,
        animationDuration: 800,
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
        'background-color': '#4A5568',
        'label': labelValue,
        'width': 'mapData(citationCount, 0, 100, 180, 280)', // Much wider for full titles
        'height': 'mapData(citationCount, 0, 100, 80, 120)', // Taller for multi-line text
        'text-valign': 'center',
        'text-halign': 'center',
        'color': '#1A202C',
        'font-size': '11px',
        'font-weight': '500',
        'font-family': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'text-wrap': 'wrap',
        'text-max-width': '300px', // Allow longer text for root nodes
        'text-overflow-wrap': 'anywhere',
        'text-transform': 'none',
        'letter-spacing': '0.015em',
        'line-height': '1.4',
        'text-margin-y': '-2px',
        'border-width': 3,
        'border-color': '#2D3748',
        'shape': 'round-rectangle',
        'text-outline-width': 1.5,
        'text-outline-color': '#FFFFFF',
        'overlay-padding': '8px',
        'text-background-color': '#FFFFFF',
        'text-background-opacity': 0.95,
        'text-background-padding': '8px 10px',
        'text-background-shape': 'roundrectangle',
        'text-background-corner-radius': '6px',
      },
    },
    {
      selector: 'node.root-node',
      style: {
        'background-color': '#000000',
        'label': labelValue,
        'width': 'mapData(citationCount, 0, 200, 200, 320)', // Much wider for full titles
        'height': 'mapData(citationCount, 0, 200, 90, 140)', // Taller for multi-line text
        'border-width': 4,
        'border-color': '#000000',
        'font-weight': '600',
        'font-size': '12px',
        'font-family': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'color': '#FFFFFF',
        'text-outline-width': 1.5,
        'text-outline-color': '#000000',
        'letter-spacing': '0.02em',
        'line-height': '1.5',
        'text-transform': 'none',
        'text-margin-y': '-2px',
      },
    },
    {
      selector: 'node.citation-node',
      style: {
        'background-color': '#718096',
        'label': labelValue,
        'width': 'mapData(citationCount, 0, 50, 160, 240)', // Much wider for full titles
        'height': 'mapData(citationCount, 0, 50, 70, 100)', // Taller for multi-line text
        'font-size': '10px',
        'font-family': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'font-weight': '500',
        'letter-spacing': '0.015em',
        'line-height': '1.4',
        'text-transform': 'none',
        'text-margin-y': '-2px',
      },
    },
    {
      selector: 'edge',
      style: {
        'width': 3, // Thicker edges for better visibility
        'line-color': '#4A5568', // Darker, more visible color
        'target-arrow-color': '#4A5568', // Match line color
        'target-arrow-shape': 'triangle',
        'target-arrow-size': 10, // Larger arrows
        'curve-style': 'bezier',
        'opacity': 0.8, // Much more visible (was 0.4)
        'control-point-step-size': 60,
        'line-style': 'solid',
        'line-cap': 'round',
      },
    },
    {
      selector: 'node:selected',
      style: {
        'background-color': '#E53E3E',
        'border-color': '#C53030',
        'border-width': 5,
        'z-index': 999,
      },
    },
    {
      selector: 'node:hover',
      style: {
        'background-color': '#2B6CB0',
        'border-color': '#2C5282',
        'border-width': 4,
        'overlay-opacity': 0.2,
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
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50 flex-wrap gap-2">
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
      <div className="flex-1 relative bg-gray-50">
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
      </div>
    </div>
  );
};

export default CitationMesh;
