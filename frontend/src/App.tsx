import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation, Navigate, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Dashboard from './pages/Dashboard';
import GraphView from './pages/GraphView';
import EvidenceVault from './pages/EvidenceVault';
import TimelineView from './pages/TimelineView';
import GeoMapView from './pages/GeoMapView';
import Login from './pages/Login';
import CaseSelection from './pages/CaseSelection';
import SemanticSearch from './pages/SemanticSearch';
import RiskScorecard from './pages/RiskScorecard';
import Watchlist from './pages/Watchlist';
import Collaboration from './pages/Collaboration';
import ReportGenerator from './pages/ReportGenerator';
import AdminPanel from './pages/AdminPanel';

import { 
  LayoutDashboard, Network, ShieldAlert, Activity, FileText, 
  Settings, Users, Database, Globe, Clock, MessageSquare, 
  Menu, Bell, Search, Terminal, ArrowLeft, ChevronRight,
  TrendingUp, Eye, ClipboardCheck, Lock
} from 'lucide-react';
import './index.css';

const PageWrapper = ({ children }: { children: React.ReactNode }) => (
  <motion.div
    initial={{ opacity: 0, y: 10, scale: 0.99 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    exit={{ opacity: 0, scale: 0.99 }}
    transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    className="h-full"
  >
    {children}
  </motion.div>
);

const CaseWorkspace = () => {
  const { id } = useParams();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  // Mock stage logic
  const stages = ['COMPLAINT', 'REVIEW', 'ASSIGNED', 'INVESTIGATION', 'CLOSURE'];
  const currentStage = 3; // INVESTIGATION

  return (
    <div className="flex h-screen bg-background text-slate-200 overflow-hidden font-sans selection:bg-blue-500/30">
      <motion.aside 
        animate={{ width: sidebarOpen ? 260 : 70 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="bg-sidebar border-r border-white/5 flex flex-col relative z-20 shrink-0"
      >
        <div className="p-4 flex items-center justify-between border-b border-white/5 h-[72px]">
          <div className="flex items-center gap-3 overflow-hidden whitespace-nowrap">
            <div className="bg-blue-500/10 p-2 rounded-lg border border-blue-500/20 shrink-0">
              <ShieldAlert size={20} className="text-blue-500" />
            </div>
            <motion.h2 
              animate={{ opacity: sidebarOpen ? 1 : 0 }}
              className="font-display font-bold tracking-widest text-lg text-white"
            >
              Nexus<span className="text-blue-500">IQ</span>
            </motion.h2>
          </div>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-slate-500 hover:text-white transition-colors shrink-0">
            <Menu size={20} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-1 custom-scrollbar">
          {sidebarOpen && (
            <NavLink to="/cases" className="flex items-center gap-2 text-slate-500 hover:text-white text-xs font-bold uppercase tracking-widest mb-4 px-3">
              <ArrowLeft size={14} /> Back to Cases
            </NavLink>
          )}
          
          <NavLink to={`/workspace/${id}`} end className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <LayoutDashboard size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Dashboard</motion.span>
          </NavLink>
          
          <NavLink to={`/workspace/${id}/graph`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Network size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Link Analysis</motion.span>
          </NavLink>

          <NavLink to={`/workspace/${id}/geo`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Globe size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Geospatial</motion.span>
          </NavLink>

          <NavLink to={`/workspace/${id}/timeline`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Clock size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Time Machine</motion.span>
          </NavLink>

          {sidebarOpen && <div className="text-xs font-bold text-slate-600 uppercase tracking-widest mb-2 mt-6 px-3">Intelligence</div>}
          
          <NavLink to={`/workspace/${id}/search`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Search size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Semantic Search</motion.span>
          </NavLink>

          <NavLink to={`/workspace/${id}/risk`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <TrendingUp size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Risk Scorecard</motion.span>
          </NavLink>

          <NavLink to={`/workspace/${id}/watchlist`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Eye size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Watchlist</motion.span>
          </NavLink>

          {sidebarOpen && <div className="text-xs font-bold text-slate-600 uppercase tracking-widest mb-2 mt-6 px-3">Operations</div>}
          
          <NavLink to={`/workspace/${id}/evidence`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Database size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Evidence Vault</motion.span>
          </NavLink>

          <NavLink to={`/workspace/${id}/collab`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Users size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Collab Room</motion.span>
          </NavLink>

          <NavLink to={`/workspace/${id}/report`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <ClipboardCheck size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Report Gen</motion.span>
          </NavLink>

          {sidebarOpen && <div className="text-xs font-bold text-slate-600 uppercase tracking-widest mb-2 mt-6 px-3">System</div>}
          <NavLink to={`/workspace/${id}/admin`} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 shadow-[inset_2px_0_0_#3b82f6]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>
            <Lock size={18} className="shrink-0" />
            <motion.span animate={{ opacity: sidebarOpen ? 1 : 0 }} className="font-medium whitespace-nowrap text-sm">Admin Panel</motion.span>
          </NavLink>
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 overflow-hidden whitespace-nowrap">
            <div className="w-8 h-8 rounded-full bg-blue-600 shrink-0 border border-white/10 flex items-center justify-center text-xs font-bold shadow-lg">01</div>
            <motion.div animate={{ opacity: sidebarOpen ? 1 : 0 }}>
              <div className="text-sm font-medium text-white">Lead Investigator</div>
              <div className="text-xs text-slate-500">Clearance: TS/SCI</div>
            </motion.div>
          </div>
        </div>
      </motion.aside>

      <div className="flex-1 flex flex-col relative z-10 h-full min-w-0">
        <header className="h-[72px] border-b border-white/5 bg-background/80 backdrop-blur-md flex items-center justify-between px-6 shrink-0 relative z-30">
          <div className="flex items-center gap-4">
            <span className="text-sm font-mono text-slate-500 bg-white/5 px-3 py-1.5 rounded-md border border-white/5">ACTIVE WORKSPACE: <strong className="text-blue-400">{id}</strong></span>
            
            {/* Investigation Workflow Progress */}
            <div className="hidden lg:flex items-center gap-2 ml-4">
              {stages.map((stage, idx) => (
                <React.Fragment key={stage}>
                  <div className={`text-[10px] font-bold px-2 py-1 rounded border ${idx < currentStage ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : idx === currentStage ? 'bg-blue-600 text-white border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'bg-transparent text-slate-600 border-slate-700'}`}>
                    {stage}
                  </div>
                  {idx < stages.length - 1 && <ChevronRight size={12} className={idx < currentStage ? 'text-blue-500' : 'text-slate-700'} />}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-xs text-slate-400 font-mono hidden sm:inline">SYSTEM SECURE</span>
            </div>
            <div className="h-6 w-px bg-white/10 mx-2"></div>
            <button className="text-slate-400 hover:text-white relative">
              <Bell size={20} />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-background"></span>
            </button>
            <button className="text-slate-400 hover:text-white">
              <Settings size={20} />
            </button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          <main className="flex-1 overflow-hidden relative bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/10 via-background to-background">
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-5 mix-blend-overlay pointer-events-none"></div>
            <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)', backgroundSize: '30px 30px' }}></div>
            
            <div className="h-full w-full p-6 relative z-10 overflow-y-auto custom-scrollbar">
              <Routes>
                <Route path="/" element={<PageWrapper><Dashboard /></PageWrapper>} />
                <Route path="/graph" element={<PageWrapper><GraphView /></PageWrapper>} />
                <Route path="/geo" element={<PageWrapper><GeoMapView /></PageWrapper>} />
                <Route path="/timeline" element={<PageWrapper><TimelineView /></PageWrapper>} />
                <Route path="/evidence" element={<PageWrapper><EvidenceVault /></PageWrapper>} />
                <Route path="/search" element={<PageWrapper><SemanticSearch /></PageWrapper>} />
                <Route path="/risk" element={<PageWrapper><RiskScorecard /></PageWrapper>} />
                <Route path="/watchlist" element={<PageWrapper><Watchlist /></PageWrapper>} />
                <Route path="/collab" element={<PageWrapper><Collaboration /></PageWrapper>} />
                <Route path="/report" element={<PageWrapper><ReportGenerator /></PageWrapper>} />
                <Route path="/admin" element={<PageWrapper><AdminPanel /></PageWrapper>} />
              </Routes>
            </div>
          </main>

        </div>
      </div>
    </div>
  );
};

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: any}> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-20 bg-slate-900 text-white h-screen overflow-auto">
          <h1 className="text-3xl font-bold text-red-500 mb-4">CRITICAL RUNTIME ERROR</h1>
          <pre className="bg-black p-6 rounded-lg text-emerald-400 font-mono text-sm border border-emerald-500/30">
            {this.state.error?.toString()}
            {this.state.error?.stack}
          </pre>
          <button 
            onClick={() => window.location.href = '/cases'}
            className="mt-8 bg-blue-600 px-6 py-3 rounded-lg font-bold"
          >
            Return to Command Center
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(localStorage.getItem('auth') === 'true');

  return (
    <Router>
      <ErrorBoundary>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route 
            path="/cases" 
            element={isAuthenticated ? <CaseSelection /> : <Navigate to="/login" replace />} 
          />
          <Route 
            path="/workspace/:id/*" 
            element={isAuthenticated ? <CaseWorkspace /> : <Navigate to="/login" replace />} 
          />
          <Route 
            path="/" 
            element={isAuthenticated ? <Navigate to="/cases" replace /> : <Navigate to="/login" replace />} 
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ErrorBoundary>
    </Router>
  );
}

export default App;

