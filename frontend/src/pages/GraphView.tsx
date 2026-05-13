import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import { Search, Filter, Maximize2, AlertTriangle, Loader2, X, Database, Activity, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const GRAPH_LAYOUT = {
  name: 'cose',
  animate: false,
  animationDuration: 1000,
  animationEasing: 'ease-out',
  nodeRepulsion: 520000,
  idealEdgeLength: 125,
  edgeElasticity: 100,
  padding: 30,
};

const ENTITY_COLORS: Record<string, string> = {
  Wallet: '#f97316',
  Email: '#38bdf8',
  Phone: '#22c55e',
  URL: '#a855f7',
  IP_Address: '#eab308',
  Person: '#ec4899',
  Unknown: '#64748b',
};

const getRiskColor = (score = 0) => {
  if (score >= 80) return '#ef4444';
  if (score >= 60) return '#f97316';
  if (score >= 40) return '#eab308';
  return '#22c55e';
};

const getEntityColor = (group = 'Unknown') => ENTITY_COLORS[group] || '#3b82f6';

const shortenLabel = (value: string, maxLength = 28) => {
  if (!value || value.length <= maxLength) return value;
  return `${value.slice(0, Math.max(8, maxLength - 9))}...${value.slice(-6)}`;
};

const GRAPH_STYLESHEET: any[] = [
  {
    selector: 'node[type="case"]',
    style: {
      'background-color': '#ef4444',
      'label': 'data(label)',
      'color': '#fff',
      'text-valign': 'bottom',
      'text-margin-y': 8,
      'font-family': 'Inter',
      'font-size': '12px',
      'width': 36,
      'height': 36,
      'border-width': 2,
      'border-color': 'rgba(239, 68, 68, 0.4)',
      'ghost': 'yes',
      'ghost-opacity': 0.3,
      'ghost-offset-x': 0,
      'ghost-offset-y': 4
    }
  },
  {
    selector: 'node[type="case"][?isRelated]',
    style: {
      'background-color': 'data(color)',
      'width': 28,
      'height': 28,
      'border-style': 'dashed',
      'border-width': 2,
      'border-color': 'rgba(255, 255, 255, 0.35)',
      'opacity': 0.85
    }
  },
  {
    selector: 'node[?isEntity]',
    style: {
      'background-color': 'data(color)',
      'label': 'data(label)',
      'color': '#94a3b8',
      'text-valign': 'bottom',
      'text-margin-y': 6,
      'font-family': 'Inter',
      'font-size': '10px',
      'width': 'mapData(caseCount, 1, 5, 22, 38)',
      'height': 'mapData(caseCount, 1, 5, 22, 38)',
      'shape': 'hexagon',
      'border-width': 1,
      'border-color': 'rgba(255, 255, 255, 0.45)'
    }
  },
  {
    selector: 'edge',
    style: {
      'width': 1.5,
      'line-color': 'rgba(255, 255, 255, 0.1)',
      'target-arrow-color': 'rgba(255, 255, 255, 0.1)',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier'
    }
  },
  {
    selector: 'edge[relation="INVOLVED_IN"]',
    style: {
      'line-color': 'rgba(148, 163, 184, 0.22)',
      'target-arrow-color': 'rgba(148, 163, 184, 0.22)'
    }
  },
  {
    selector: 'edge[relation="CONNECTED_TO"]',
    style: {
      'width': 1,
      'line-color': 'rgba(59, 130, 246, 0.16)',
      'target-arrow-shape': 'none',
      'line-style': 'dotted'
    }
  },
  {
    selector: 'edge[relation="RELATED_TO"]',
    style: {
      'width': 'mapData(score, 0, 1, 1.5, 6)',
      'line-color': 'rgba(248, 113, 113, 0.7)',
      'target-arrow-color': 'rgba(248, 113, 113, 0.7)',
      'line-style': 'solid'
    }
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#fbbf24',
      'shadow-blur': 20,
      'shadow-color': '#fbbf24',
      'shadow-opacity': 0.8
    }
  }
];

const GraphView = () => {
  const { id } = useParams();
  const refreshKey = useWorkspaceRefresh(id);
  const [elements, setElements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ nodes: 0, edges: 0 });
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedEdge, setSelectedEdge] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterEnabled, setFilterEnabled] = useState(false);
  const cyRef = useRef<any>(null);

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/graph/${id}`);
        const data = await res.json();
        
        if (data.nodes && data.edges) {
          const els: any[] = [];
          
          data.nodes.forEach((n: any) => {
            const properties = n.properties || {};
            const group = n.label || 'Unknown';
            const isCase = group === 'Case';
            const label = String(properties.value || properties.address || properties.ip || properties.mac || properties.name || properties.id || group);
            const riskScore = Number(properties.risk_score || 0);

            els.push({
              data: { 
                id: n.id, 
                label: shortenLabel(label), 
                fullLabel: label,
                type: isCase ? 'case' : 'entity',
                isEntity: !isCase,
                isRelated: Boolean(properties.related),
                group,
                color: isCase ? getRiskColor(riskScore) : getEntityColor(group),
                riskScore,
                caseCount: Number(properties.case_count || 1),
                similarity: Number(properties.similarity || 0),
              }
            });
          });
          
          data.edges.forEach((l: any, idx: number) => {
            els.push({
              data: {
                id: l.id || `edge_${idx}`,
                source: l.source,
                target: l.target,
                label: l.type,
                relation: l.type,
                score: Number(l.score || 0),
                sharedEntities: l.shared_entities || [],
              }
            });
          });
          
          setElements(els);
          setStats({ nodes: data.nodes.length, edges: data.edges.length });
        }
      } catch (err) {
        console.error("Failed to fetch graph data:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchGraphData();
  }, [id, refreshKey]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value.toLowerCase();
    setSearchQuery(q);
    
    if (!cyRef.current) return;
    
    if (q === '') {
      cyRef.current.elements().style({ opacity: 1 });
      return;
    }
    
    cyRef.current.elements().style({ opacity: 0.15 });
    const matched = cyRef.current.nodes().filter((n: any) => {
      const label = String(n.data('label') || '').toLowerCase();
      const group = String(n.data('group') || '').toLowerCase();
      
      // Prevent single letters like 'e' or 'a' from matching the word 'Case' and highlighting the whole network
      if (group === 'case' && q.length < 4) {
        return label.includes(q);
      }
      
      return label.includes(q) || group.includes(q);
    });
    
    if (matched.length > 0) {
      // Highlight ONLY the specifically matched nodes to prevent network blowout
      matched.style({ opacity: 1 });
      
      // Optionally show the connecting lines faintly, but DO NOT highlight the connected nodes
      matched.connectedEdges().style({ opacity: 0.4 });
    }
  };

  const toggleFilter = () => {
    if (!cyRef.current) return;
    const nextState = !filterEnabled;
    setFilterEnabled(nextState);
    
    if (!nextState) {
      cyRef.current.elements().style({ display: 'element' });
      // cyRef.current.fit();
    } else {
      // Hide nodes that only have 1 edge (leaves) to show only the "core" ring
      const leaves = cyRef.current.nodes().filter((n: any) => n.degree() <= 1 && n.data('type') !== 'case');
      leaves.style({ display: 'none' });
      // cyRef.current.fit();
    }
  };

  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      {/* Header Panel */}
      <div className="flex justify-between items-end shrink-0">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="bg-red-500/20 text-red-400 text-xs font-bold px-2 py-1 rounded border border-red-500/30 flex items-center gap-1">
              <AlertTriangle size={12} /> {stats.edges > 0 ? 'CRITICAL NETWORK' : 'ISOLATED'}
            </span>
          </div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-1">Entity Link Analysis</h1>
          <p className="text-slate-400 text-sm">Visualizing connections for {id}</p>
        </div>
        
        <div className="glass-panel flex gap-6 px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>
            <span className="text-sm font-medium text-slate-300">Nodes ({stats.nodes})</span>
          </div>
          <div className="w-px bg-white/10"></div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}></div>
            <span className="text-sm font-medium text-slate-300">Relationships ({stats.edges})</span>
          </div>
        </div>
      </div>

      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="glass-panel flex-1 relative overflow-hidden flex min-h-[500px]">
        
        {/* Controls Overlay */}
        <div className="absolute top-6 left-6 z-10 flex gap-3">
          <div className="bg-[#05070a]/90 backdrop-blur-md border border-white/10 rounded-lg p-2 flex items-center gap-2 shadow-xl focus-within:border-blue-500/50 transition-colors">
            <Search size={16} className="text-slate-400 ml-1" />
            <input 
              type="text" 
              placeholder="Search ID or Type (e.g. Email)..." 
              value={searchQuery}
              onChange={handleSearch}
              className="bg-transparent border-none outline-none text-sm w-56 px-2 text-white placeholder-slate-600" 
            />
          </div>
          <button 
            onClick={toggleFilter}
            className={`backdrop-blur-md border transition-colors rounded-lg p-2 px-4 flex items-center gap-2 shadow-xl ${filterEnabled ? 'bg-blue-500/20 border-blue-500/50 text-blue-400' : 'bg-[#05070a]/90 border-white/10 hover:bg-white/5 text-slate-300 hover:text-white'}`}
          >
            <Filter size={16} />
            <span className="text-sm font-medium">Core Nodes Only</span>
          </button>
          <button className="bg-[#05070a]/90 backdrop-blur-md border border-white/10 hover:bg-white/5 transition-colors rounded-lg p-2.5 shadow-xl text-slate-300 hover:text-white" onClick={() => cyRef.current?.fit()}>
            <Maximize2 size={16} />
          </button>
        </div>

        {/* Graph Render Area */}
        <div className="w-full h-full bg-[#05070a] flex items-center justify-center">
          {/* Ambient background grid inside the graph */}
          <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(59, 130, 246, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(59, 130, 246, 0.05) 1px, transparent 1px)', backgroundSize: '50px 50px', backgroundPosition: 'center center' }}></div>
          
          {loading ? (
            <div className="flex flex-col items-center gap-4 z-20">
              <Loader2 className="animate-spin text-blue-500" size={40} />
              <div className="font-mono text-sm text-blue-400">CONNECTING TO NEO4J GRAPH ENGINE...</div>
            </div>
          ) : elements.length > 0 && (
            <CytoscapeComponent 
              elements={elements} 
              layout={GRAPH_LAYOUT} 
              stylesheet={GRAPH_STYLESHEET}
              style={{ width: '100%', height: '100%' }} 
              cy={(cy) => {
                cyRef.current = cy;
                // Add interactivity
                cy.on('tap', 'node', function(evt){
                  setSelectedEdge(null);
                  const node = evt.target;
                  setSelectedNode(node.data());
                  // Pulse animation on click
                  node.animate({
                    style: { 'border-width': 4, 'border-color': '#fbbf24' }
                  }, { duration: 200 }).animate({
                    style: { 'border-width': node.data('isEntity') ? 1 : 2, 'border-color': node.data('isEntity') ? '#60a5fa' : 'rgba(239, 68, 68, 0.4)' }
                  }, { duration: 200 });
                });
                
                cy.on('tap', 'edge', function(evt){
                  setSelectedNode(null);
                  const edge = evt.target;
                  const sourceNode = cy.getElementById(edge.data('source'));
                  const targetNode = cy.getElementById(edge.data('target'));
                  
                  let explanation = `This connection represents a ${edge.data('relation')} relationship.`;
                  if (edge.data('relation') === 'RELATED_TO') {
                    // XAI: Explain why cases are linked using backend-computed shared entities
                    const sharedList = edge.data('sharedEntities') || [];
                    const commonEntities = sharedList.length > 0 ? sharedList.join(', ') : 'Unknown';
                    explanation = `NexusIQ AI linked these cases because they share identical entities found in evidence: ${commonEntities}.`;
                  }

                  setSelectedEdge({
                    ...edge.data(),
                    sourceLabel: sourceNode.data('label'),
                    targetLabel: targetNode.data('label'),
                    explanation
                  });
                });

                // Deselect when clicking background
                cy.on('tap', function(evt){
                  if(evt.target === cy){
                    setSelectedNode(null);
                    setSelectedEdge(null);
                  }
                });
              }}
            />
          )}
        </div>
        
        {/* Node/Edge Details Overlay Panel */}
        <AnimatePresence>
          {selectedEdge && (
            <motion.div 
              initial={{ opacity: 0, x: 20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 20, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute top-6 right-6 z-20 w-80 glass-panel border border-white/10 rounded-xl overflow-hidden shadow-2xl flex flex-col"
            >
              <div className="p-4 border-b border-white/5 flex items-center justify-between bg-blue-500/10">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg shadow-inner bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    <Activity size={18} />
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-white leading-tight">AI Link Explanation</h3>
                    <p className="text-[10px] font-mono tracking-widest uppercase mt-0.5 text-blue-400">NETWORK EDGE</p>
                  </div>
                </div>
                <button onClick={() => setSelectedEdge(null)} className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-white/10 transition-colors">
                  <X size={16} />
                </button>
              </div>
              
              <div className="p-5 flex-1 bg-black/40">
                <div className="mb-4">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">RELATIONSHIP</label>
                  <div className="font-mono text-sm text-slate-200 bg-white/5 p-2.5 rounded-lg border border-white/5 shadow-inner">
                    {selectedEdge.sourceLabel} ➔ {selectedEdge.targetLabel}
                  </div>
                </div>
                <div className="mb-6">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2 text-blue-400 flex items-center gap-1">
                    <Shield size={12} /> EXPLAINABLE AI REASONING
                  </label>
                  <div className="text-sm text-slate-300 bg-blue-900/20 p-3 rounded-lg border border-blue-500/20 leading-relaxed italic">
                    "{selectedEdge.explanation}"
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {selectedNode && (
            <motion.div 
              initial={{ opacity: 0, x: 20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 20, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute top-6 right-6 z-20 w-80 glass-panel border border-white/10 rounded-xl overflow-hidden shadow-2xl flex flex-col"
            >
              <div className={`p-4 border-b border-white/5 flex items-center justify-between ${selectedNode.isEntity ? 'bg-blue-500/10' : 'bg-red-500/10'}`}>
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg shadow-inner ${selectedNode.isEntity ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                    {selectedNode.isEntity ? <Database size={18} /> : <Shield size={18} />}
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-white leading-tight">
                      {selectedNode.isEntity ? 'Target Profile' : 'Case Profile'}
                    </h3>
                    <p className={`text-[10px] font-mono tracking-widest uppercase mt-0.5 ${selectedNode.isEntity ? 'text-blue-400' : 'text-red-400'}`}>
                    {selectedNode.isEntity ? 'EVIDENCE NODE' : selectedNode.isRelated ? 'RELATED CASE' : 'CASE RECORD'}
                    </p>
                  </div>
                </div>
                <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-white/10 transition-colors">
                  <X size={16} />
                </button>
              </div>
              
              <div className="p-5 flex-1 bg-black/40">
                <div className="mb-4">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">CATEGORY / TYPE</label>
                  <div className="font-mono text-sm text-slate-200 bg-white/5 p-2.5 rounded-lg border border-white/5 shadow-inner flex items-center gap-2">
                    {selectedNode.isEntity ? <Database size={14} className="text-blue-400" /> : <Shield size={14} className="text-red-400" />}
                    {selectedNode.group || 'Unknown'}
                  </div>
                </div>

                <div className="mb-4">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">IDENTIFIER / VALUE</label>
                  <div className="font-mono text-sm text-slate-200 bg-white/5 p-2.5 rounded-lg border border-white/5 break-all shadow-inner">
                    {selectedNode.fullLabel || selectedNode.label}
                  </div>
                </div>
                {!selectedNode.isEntity && (
                  <div className="mb-4">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">RISK SCORE</label>
                    <div className="font-mono text-sm text-slate-200 bg-white/5 p-2.5 rounded-lg border border-white/5 shadow-inner">
                      {selectedNode.riskScore}/100
                    </div>
                  </div>
                )}
                {selectedNode.isEntity && (
                  <div className="mb-4">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">CASE APPEARANCES</label>
                    <div className="font-mono text-sm text-slate-200 bg-white/5 p-2.5 rounded-lg border border-white/5 shadow-inner">
                      {selectedNode.caseCount}
                    </div>
                  </div>
                )}
                
                <div className="mb-6">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">SYSTEM ID</label>
                  <div className="font-mono text-[10px] text-slate-400 truncate bg-black/30 p-2 rounded border border-white/5">
                    {selectedNode.id}
                  </div>
                </div>
                
                <button className="w-full py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-bold text-white flex items-center justify-center gap-2 transition-colors shadow-lg">
                  <Activity size={16} className={selectedNode.isEntity ? "text-blue-400" : "text-red-400"} /> 
                  {selectedNode.isEntity ? 'Run Deep Trace' : 'View Case File'}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
      </motion.div>
    </div>
  );
};

export default GraphView;
