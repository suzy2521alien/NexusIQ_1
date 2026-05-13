import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search, FolderOpen, Activity, ShieldAlert, LogOut, PlusCircle, CheckCircle,
  FileText, UploadCloud, X, Loader2, AlertCircle
} from 'lucide-react';

const CaseSelection = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<{role: string, name: string, badgeId: string} | null>(null);

  useEffect(() => {
    const session = localStorage.getItem('nexus_user');
    if (session) {
      setUser(JSON.parse(session));
    } else {
      navigate('/login');
    }
  }, [navigate]);

  const [allCases, setAllCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dbError, setDbError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('ALL');
  const [showCreateCase, setShowCreateCase] = useState(false);
  const [creatingCase, setCreatingCase] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [initialEvidence, setInitialEvidence] = useState<File | null>(null);
  const [createForm, setCreateForm] = useState({
    case_id: '',
    title: '',
    assignedTo: 'Lead Investigator',
    priority: 'MEDIUM',
    stage: 'COMPLAINT',
    notes: ''
  });

  const fetchCases = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/cases/list');
      if (!res.ok) {
        throw new Error(`Backend Database Connection Failed (Status: ${res.status})`);
      }

      const data = await res.json();
      const backendCases = data.cases.map((caseItem: any) => ({
        id: caseItem.id,
        title: caseItem.title || `Forensic Case: ${caseItem.id.split('-').pop()}`,
        threatLevel: caseItem.risk_score >= 80 ? 'CRITICAL' : caseItem.risk_score >= 60 ? 'HIGH' : caseItem.risk_score >= 40 ? 'MEDIUM' : 'LOW',
        stage: caseItem.stage || (caseItem.risk_score >= 80 ? 'INVESTIGATION' : caseItem.risk_score >= 60 ? 'ASSIGNED' : caseItem.risk_score >= 40 ? 'REVIEW' : 'COMPLAINT'),
        riskScore: caseItem.risk_score || 0,
        entitiesCount: caseItem.entity_count || 0,
        linkedCases: caseItem.linked_cases || 0,
        lastActive: caseItem.updated_at || caseItem.created_at ? new Date(caseItem.updated_at || caseItem.created_at).toLocaleDateString() : 'N/A',
        status: caseItem.status,
        assignedTo: caseItem.assignedTo || 'Unassigned'
      }));

      setAllCases(backendCases);
      setDbError(null);
    } catch (err: any) {
      console.error("Backend error:", err);
      setDbError(err.message || "CRITICAL FAILURE: Unable to establish secure connection to Neo4j Graph Database.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const generateCaseId = () => {
    const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const suffix = Math.random().toString(16).slice(2, 6).toUpperCase();
    return `CASE-${stamp}-${suffix}`;
  };

  const openCreateModal = (stage = 'COMPLAINT') => {
    const caseId = generateCaseId();
    setCreateForm({
      case_id: caseId,
      title: `Forensic Case: ${caseId.split('-').pop()}`,
      assignedTo: user?.name || 'Lead Investigator',
      priority: stage === 'INVESTIGATION' ? 'HIGH' : 'MEDIUM',
      stage,
      notes: ''
    });
    setInitialEvidence(null);
    setCreateError(null);
    setShowCreateCase(true);
  };

  const createCase = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingCase(true);
    setCreateError(null);

    try {
      const res = await fetch('http://localhost:8000/cases/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...createForm,
          status: createForm.stage === 'COMPLAINT' ? 'COMPLAINT' : 'INVESTIGATION',
          created_by: user?.name || 'Lead Investigator'
        })
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Unable to create case');
      }

      const data = await res.json();
      const newCaseId = data.case?.id || createForm.case_id;

      if (initialEvidence) {
        const formData = new FormData();
        formData.append('files', initialEvidence);
        formData.append('case_id', newCaseId);
        formData.append('officer', user?.name || 'Lead Investigator');
        formData.append('source', 'Initial case creation intake');

        const uploadRes = await fetch('http://localhost:8000/evidence/upload', {
          method: 'POST',
          body: formData
        });

        if (!uploadRes.ok) {
          const error = await uploadRes.json().catch(() => ({}));
          throw new Error(error.detail || 'Case created, but initial evidence upload failed');
        }
      }

      setShowCreateCase(false);
      await fetchCases();
      navigate(`/workspace/${newCaseId}`);
    } catch (err) {
      console.error("Create case error:", err);
      setCreateError(err instanceof Error ? err.message : 'Unable to create case');
    } finally {
      setCreatingCase(false);
    };
  };

  if (!user) return null;

  // Role Filtering Logic
  let displayCases = allCases;
  if (user.role === 'INTAKE') {
    displayCases = allCases.filter(c => c.status === 'COMPLAINT');
  } else if (user.role === 'ADMIN' || user.role === 'INVESTIGATOR') {
    if (activeTab === 'ACTIVE') displayCases = allCases.filter(c => c.status === 'INVESTIGATION');
    else if (activeTab === 'PENDING') displayCases = allCases.filter(c => c.status === 'COMPLAINT');
    else if (activeTab === 'ARCHIVED') displayCases = allCases.filter(c => c.status === 'ARCHIVED');
    else displayCases = allCases; // Show ALL for 'ALL' tab
  }

  const getStageColor = (stage: string) => {
    switch(stage) {
      case 'INVESTIGATION': return 'text-red-500 border-red-500/30 bg-red-500/10';
      case 'ASSIGNED': return 'text-orange-500 border-orange-500/30 bg-orange-500/10';
      case 'REVIEW': return 'text-yellow-500 border-yellow-500/30 bg-yellow-500/10';
      case 'COMPLAINT': return 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10';
      default: return 'text-blue-500 border-blue-500/30 bg-blue-500/10';
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('nexus_user');
    navigate('/login');
  };

  return (
    <div className="h-screen overflow-y-auto bg-background text-slate-200 p-8 custom-scrollbar">
      {/* Top Bar */}
      <header className="flex justify-between items-center mb-10 pb-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <ShieldAlert size={28} className={user.role === 'ADMIN' ? "text-purple-500" : user.role === 'INTAKE' ? "text-emerald-500" : "text-blue-500"} />
          <h1 className="text-2xl font-display font-bold tracking-widest text-white">Nexus<span className={user.role === 'ADMIN' ? "text-purple-500" : user.role === 'INTAKE' ? "text-emerald-500" : "text-blue-500"}>IQ</span></h1>
          <span className="ml-4 px-2 py-1 bg-white/5 border border-white/10 rounded text-xs font-mono text-slate-400">
            {user.role} MODE
          </span>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 border-l border-white/10 pl-6">
            <div className="text-right">
              <div className="text-sm font-bold text-white">{user.name}</div>
              <div className="text-xs text-slate-500 font-mono">{user.badgeId}</div>
            </div>
            <button onClick={handleLogout} className="p-2 hover:bg-white/5 rounded-lg text-slate-400 hover:text-red-400 transition-colors">
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto">
        
        {/* INTAKE OFFICER SPECIFIC VIEW */}
        {user.role === 'INTAKE' ? (
          <>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-3xl font-display font-bold text-white mb-2">Complaint / FIR Intake</h2>
                <p className="text-slate-400">Log citizen complaints, upload initial evidence, and submit for Supervisor review.</p>
              </div>
              <button
                onClick={() => openCreateModal('COMPLAINT')}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-lg font-bold flex items-center gap-2 transition-colors shadow-lg"
              >
                <PlusCircle size={20} /> File New Complaint (FIR)
              </button>
            </div>
            
            <div className="glass-panel p-6 mb-8 border-dashed border-emerald-500/30 bg-emerald-500/5 flex flex-col items-center justify-center text-center">
               <FileText size={48} className="text-emerald-400 mb-4 opacity-50" />
               <h3 className="font-display font-bold text-lg text-white mb-2">Quick Evidence Drop</h3>
               <p className="text-sm text-slate-400 mb-4 max-w-md">Drag and drop raw evidence files (WhatsApp exports, Screenshots, CSVs) to automatically parse entities and generate a draft FIR.</p>
               <button onClick={() => openCreateModal('COMPLAINT')} className="px-4 py-2 border border-emerald-500/50 rounded-lg text-emerald-400 hover:bg-emerald-500/10 transition-colors text-sm font-bold">Browse Local Files</button>
            </div>
            
            <h3 className="font-display font-bold text-xl text-white mb-4">Pending Complaints Awaiting Review</h3>
          </>
        ) : (
          <>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-3xl font-display font-bold text-white mb-2">
                  {user.role === 'ADMIN' ? 'Command Center Overview' : 'Intelligence Workspace Access'}
                </h2>
                <p className="text-slate-400">
                  Select an active case below to enter the **Forensic Intelligence Workspace**. Once inside, you can run Link Analysis, extract entities from the Vault, and collaborate with other investigators.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => openCreateModal('INVESTIGATION')}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-3 rounded-lg font-bold flex items-center gap-2 transition-colors shadow-lg shadow-blue-600/20"
                >
                  <PlusCircle size={18} /> New Case
                </button>
                <div className="bg-[#05070a] border border-white/10 rounded-lg p-2 flex items-center gap-2 focus-within:border-blue-500/50 w-64">
                  <Search size={16} className="text-slate-400 ml-1" />
                  <input type="text" placeholder="Search case ID or entity..." className="bg-transparent border-none outline-none text-sm w-full text-white" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
              <div className="glass-panel p-5 border-l-2 border-blue-500 bg-blue-500/5">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Dept Cases</span>
                  <Activity size={14} className="text-blue-400" />
                </div>
                <div className="text-3xl font-display font-bold text-white">{allCases.length}</div>
                <div className="text-[10px] text-blue-400 font-mono mt-1">Live from Neo4j Aura</div>
              </div>
              
              <div className="glass-panel p-5 border-l-2 border-red-500 bg-red-500/5">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Critical Threats</span>
                  <ShieldAlert size={14} className="text-red-400" />
                </div>
                <div className="text-3xl font-display font-bold text-red-500">{allCases.filter(c => c.riskScore >= 80).length}</div>
                <div className="text-[10px] text-red-400 font-mono mt-1">Requires immediate LEO action</div>
              </div>

              <div className="glass-panel p-5 border-l-2 border-purple-500 bg-purple-500/5">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Pending Ingest</span>
                  <PlusCircle size={14} className="text-purple-400" />
                </div>
                <div className="text-3xl font-display font-bold text-purple-400">{allCases.filter(c => c.status === 'COMPLAINT').length}</div>
                <div className="text-[10px] text-purple-400 font-mono mt-1">Awaiting Supervisor review</div>
              </div>

              <div className="glass-panel p-5 border-l-2 border-emerald-500 bg-emerald-500/5">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">System Health</span>
                  <div className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </div>
                </div>
                <div className="text-xl font-mono font-bold text-emerald-400 mt-2 uppercase tracking-tight">NOMINAL</div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Lat: 12ms | Cluster: US-East</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between mb-6">
               <div className="flex gap-4">
                 <button onClick={() => setActiveTab('ALL')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'ALL' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>All Department Files</button>
                 <button onClick={() => setActiveTab('ACTIVE')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'ACTIVE' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>Active Investigations</button>
                 <button onClick={() => setActiveTab('PENDING')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'PENDING' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>Pending Review</button>
               </div>
               <div className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
                 Showing {displayCases.length} of {allCases.length} artifacts
               </div>
            </div>
          </>
        )}

        {/* Case List */}
        <div className="flex flex-col gap-4">
          {loading && (
            <div className="glass-panel p-8 text-center text-xs text-slate-500 font-mono uppercase tracking-widest">
              Loading case registry...
            </div>
          )}
          {!loading && dbError && (
            <div className="glass-panel p-5 border border-red-500/20 bg-red-500/5 flex items-start gap-3">
              <AlertCircle size={18} className="text-red-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold text-red-300">Case registry unavailable</div>
                <div className="text-xs text-slate-400 mt-1">{dbError}</div>
              </div>
            </div>
          )}
          {!loading && !dbError && displayCases.length === 0 && (
            <div className="glass-panel p-10 border border-dashed border-white/10 text-center">
              <FolderOpen size={42} className="text-slate-600 mx-auto mb-4" />
              <h3 className="font-display font-bold text-xl text-white mb-2">No cases in this queue</h3>
              <button onClick={() => openCreateModal(user.role === 'INTAKE' ? 'COMPLAINT' : 'INVESTIGATION')} className="mt-4 bg-blue-600 hover:bg-blue-500 text-white px-5 py-3 rounded-lg font-bold inline-flex items-center gap-2 transition-colors">
                <PlusCircle size={18} /> Create Case
              </button>
            </div>
          )}
          {displayCases.map((c, idx) => (
            <motion.div 
              key={c.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              onClick={(e) => {
                if ((e.target as HTMLElement).closest('button')) return;
                // Only investigators and admins enter the graph workspace
                if (user.role !== 'INTAKE') {
                   navigate(`/workspace/${c.id}`);
                }
              }}
              className={`glass-panel p-5 flex items-center justify-between hover:bg-white/[0.03] transition-all border-l-4 group ${user.role !== 'INTAKE' ? 'cursor-pointer' : ''}`}
              style={{ borderLeftColor: c.status === 'ARCHIVED' ? '#64748b' : c.stage === 'INVESTIGATION' ? '#ef4444' : c.stage === 'ASSIGNED' ? '#f97316' : c.stage === 'REVIEW' ? '#eab308' : '#10b981' }}
            >
              <div className="flex items-center gap-6">
                <div className={`p-3 rounded-lg border group-hover:scale-110 transition-transform ${c.status === 'ARCHIVED' ? 'bg-slate-800 border-slate-700' : 'bg-white/5 border-white/5'}`}>
                  {c.status === 'ARCHIVED' ? <CheckCircle size={24} className="text-slate-500" /> : <FolderOpen size={24} className="text-blue-400" />}
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-mono text-xs text-slate-400">{c.id}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${c.status === 'ARCHIVED' ? 'text-slate-400 border-slate-600 bg-slate-800' : getStageColor(c.stage)}`}>
                      {c.status === 'ARCHIVED' ? 'RESOLVED & ARCHIVED' : `STAGE: ${c.stage}`}
                    </span>
                    {c.status === 'COMPLAINT' && c.stage !== 'COMPLAINT' && (
                       <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider text-purple-400 border-purple-500/30 bg-purple-500/10">
                         PENDING REVIEW
                       </span>
                    )}
                  </div>
                  <h3 className={`text-xl font-display font-bold transition-colors ${c.status === 'ARCHIVED' ? 'text-slate-500' : 'text-white group-hover:text-blue-400'}`}>{c.title}</h3>
                </div>
              </div>

              <div className="flex items-center gap-8">

                


                {user.role === 'INTAKE' && c.status === 'COMPLAINT' && (
                  <button className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors">
                    Edit FIR Data
                  </button>
                )}

                {user.role !== 'INTAKE' && (
                  <>
                    <div className="flex flex-col items-center">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Risk Score</span>
                      <span className={`font-mono text-lg font-bold ${c.status === 'ARCHIVED' ? 'text-slate-600' : 'text-white'}`}>{c.riskScore}/100</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Shared Entities</span>
                      <span className={`font-mono text-lg font-bold ${c.status === 'ARCHIVED' ? 'text-slate-600' : 'text-blue-400'}`}>{c.entitiesCount}</span>
                    </div>
                    <div className="flex flex-col items-end w-24">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Last Update</span>
                      <span className="text-sm text-slate-400">{c.lastActive}</span>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {showCreateCase && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/70 backdrop-blur-md">
          <motion.form
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={createCase}
            className="glass-panel w-full max-w-3xl p-8 border-white/10 shadow-[0_0_60px_rgba(0,0,0,0.5)]"
          >
            <div className="flex items-start justify-between mb-8">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-blue-600 rounded-xl shadow-lg shadow-blue-600/20">
                    <PlusCircle size={22} className="text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-display font-bold text-white">Create New Case</h2>
                    <p className="text-xs text-slate-500 uppercase tracking-widest font-bold">Registry + optional initial ingest</p>
                  </div>
                </div>
              </div>
              <button type="button" onClick={() => setShowCreateCase(false)} className="text-slate-500 hover:text-white transition-colors">
                <X size={24} />
              </button>
            </div>

            {createError && (
              <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
                <AlertCircle size={18} className="text-red-400 shrink-0 mt-0.5" />
                <p className="text-xs text-red-200">{createError}</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Case ID</label>
                <input
                  required
                  type="text"
                  value={createForm.case_id}
                  onChange={(e) => setCreateForm({ ...createForm, case_id: e.target.value })}
                  className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Assigned Investigator</label>
                <input
                  type="text"
                  value={createForm.assignedTo}
                  onChange={(e) => setCreateForm({ ...createForm, assignedTo: e.target.value })}
                  className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Case Title</label>
                <input
                  required
                  type="text"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Initial Stage</label>
                <select
                  value={createForm.stage}
                  onChange={(e) => setCreateForm({ ...createForm, stage: e.target.value })}
                  className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all"
                >
                  <option value="COMPLAINT">Complaint Intake</option>
                  <option value="REVIEW">Review</option>
                  <option value="ASSIGNED">Assigned</option>
                  <option value="INVESTIGATION">Investigation</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Priority</label>
                <select
                  value={createForm.priority}
                  onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
                  className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all"
                >
                  <option>LOW</option>
                  <option>MEDIUM</option>
                  <option>HIGH</option>
                  <option>CRITICAL</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Case Notes</label>
                <textarea
                  value={createForm.notes}
                  onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                  rows={3}
                  className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all resize-none"
                />
              </div>
            </div>

            <label className="block border border-dashed border-white/10 rounded-xl p-5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer mb-8">
              <input
                type="file"
                className="hidden"
                onChange={(e) => setInitialEvidence(e.target.files?.[0] || null)}
              />
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/5 rounded-xl">
                  <UploadCloud size={22} className="text-blue-400" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-bold text-white">{initialEvidence ? initialEvidence.name : 'Attach initial evidence now'}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {initialEvidence ? `${(initialEvidence.size / 1024).toFixed(1)} KB selected` : 'Optional. You can also upload evidence later from the Evidence Vault.'}
                  </div>
                </div>
              </div>
            </label>

            <div className="flex gap-4">
              <button type="button" onClick={() => setShowCreateCase(false)} className="flex-1 bg-white/5 hover:bg-white/10 py-4 rounded-xl text-xs font-bold text-slate-400 uppercase tracking-widest transition-all">
                Cancel
              </button>
              <button type="submit" disabled={creatingCase} className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed py-4 rounded-xl text-xs font-bold text-white uppercase tracking-widest transition-all shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2">
                {creatingCase ? <Loader2 size={16} className="animate-spin" /> : <PlusCircle size={16} />}
                Create Case
              </button>
            </div>
          </motion.form>
        </div>
      )}
    </div>
  );
};

export default CaseSelection;
