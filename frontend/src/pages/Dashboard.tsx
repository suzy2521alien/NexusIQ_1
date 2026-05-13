import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { 
  AlertTriangle, Fingerprint, Activity, FileText, TrendingUp, 
  ShieldAlert, Zap, Users, Wallet, Search, Bell, 
  ChevronRight, ArrowUpRight, Clock, Shield
} from 'lucide-react';

const Dashboard = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const refreshKey = useWorkspaceRefresh(id);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const watchDotClasses: Record<string, string> = {
    red: 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]',
    blue: 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]',
    orange: 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]'
  };
  const [error, setError] = useState<string | null>(null);
  const [showAlert, setShowAlert] = useState(true);
  const [inferenceText, setInferenceText] = useState<string | null>(null);
  const [loadingInference, setLoadingInference] = useState(false);

  useEffect(() => {
    const fetchCaseData = async () => {
      try {
        setLoading(true);
        const res = await fetch(`http://localhost:8000/cases/${id}`);
        if (!res.ok) throw new Error('Failed to fetch intelligence data');
        const caseData = await res.json();
        setData(caseData);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchCaseData();
  }, [id, refreshKey]);

  const fetchInference = async () => {
    setLoadingInference(true);
    try {
      const res = await fetch(`http://localhost:8000/intelligence/inference/${id}`);
      if (res.ok) {
        const data = await res.json();
        setInferenceText(data.inference);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingInference(false);
    }
  };

  if (loading) return <div className="p-8 text-slate-400 flex items-center gap-3"><Activity className="animate-spin" /> Loading intelligence data...</div>;
  if (error) return <div className="p-8 text-red-400">Error: {error}</div>;
  if (!data) return <div className="p-8 text-slate-400">No data found for this case.</div>;

  const { 
    risk_assessment = { score: 0, level: 'LOW', reasons: [], trigger_words: [] }, 
    intent = { labels: [], confidence: 0 }, 
    entities = { wallets: [], emails: [], phones: [], urls: [] }, 
    case_id = id 
  } = data || {};

  const highlightTriggerWords = (text: string, words: string[]) => {
    if (!words || words.length === 0 || !text) return text;
    
    // Sort words by length descending to match longest phrases first
    const sortedWords = [...words].sort((a, b) => b.length - a.length);
    const escapedWords = sortedWords.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const pattern = new RegExp(`(${escapedWords.join('|')})`, 'gi');
    
    const parts = text.split(pattern);
    
    return parts.map((part, i) => {
      const isMatch = sortedWords.some(w => w.toLowerCase() === part.toLowerCase());
      if (isMatch) {
        return <mark key={i} className="bg-red-500/30 text-red-400 font-bold px-1 rounded" title="AI Trigger Word">{part}</mark>;
      }
      return <React.Fragment key={i}>{part}</React.Fragment>;
    });
  };

  const getRiskStyles = (level: string) => {
    switch(level) {
      case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/30';
      case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
      default: return 'text-green-500 bg-green-500/10 border-green-500/30';
    }
  };

  const riskStyle = getRiskStyles(risk_assessment.level);
  const entityTotal = Object.values(entities).flat().length;
  const primaryEntity =
    entities.wallets?.[0] ||
    entities.emails?.[0] ||
    entities.phones?.[0] ||
    entities.urls?.[0] ||
    case_id;
  const statCards = [
    { label: 'Evidence Files', value: String(data.evidence_count || data.hashes?.length || 0).padStart(2, '0'), icon: FileText, iconClass: 'text-blue-500', panelClass: 'bg-blue-500/10 border-blue-500/20', change: 'live' },
    { label: 'Wallets Flagged', value: String(entities.wallets?.length || 0).padStart(2, '0'), icon: Wallet, iconClass: 'text-purple-500', panelClass: 'bg-purple-500/10 border-purple-500/20', change: 'live' },
    { label: 'Entities Found', value: String(entityTotal).padStart(2, '0'), icon: Fingerprint, iconClass: 'text-emerald-500', panelClass: 'bg-emerald-500/10 border-emerald-500/20', change: 'live' },
    { label: 'Risk Score', value: String(risk_assessment.score || 0).padStart(2, '0'), icon: AlertTriangle, iconClass: 'text-orange-500', panelClass: 'bg-orange-500/10 border-orange-500/20', change: risk_assessment.level },
  ];
  const watchItems = [
    ...(entities.wallets || []).map((value: string) => ({ name: value, type: 'Wallet', color: 'red' })),
    ...(entities.emails || []).map((value: string) => ({ name: value, type: 'Email', color: 'blue' })),
    ...(entities.phones || []).map((value: string) => ({ name: value, type: 'Phone', color: 'orange' })),
  ].slice(0, 5);

  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      {/* High-Risk Alerts Banner */}
      <AnimatePresence>
        {showAlert && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-gradient-to-r from-red-600/20 to-orange-600/20 border border-red-500/30 rounded-xl p-4 flex items-center justify-between backdrop-blur-md">
              <div className="flex items-center gap-4">
                <div className="bg-red-500 animate-pulse p-2 rounded-full shadow-[0_0_15px_rgba(239,68,68,0.5)]">
                  <Bell size={18} className="text-white" />
                </div>
                <div>
                  <h4 className="text-red-400 font-bold text-sm uppercase tracking-wider">High Priority Alert</h4>
                  <p className="text-white text-sm font-medium">
                    Backend risk engine flagged {risk_assessment.reasons?.[0] || 'case activity'} linked to <span className="font-mono text-blue-400">{primaryEntity}</span>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button className="bg-red-500 hover:bg-red-600 text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors">INVESTIGATE NOW</button>
                <button onClick={() => setShowAlert(false)} className="text-slate-500 hover:text-white transition-colors">
                  <Zap size={18} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => (
          <motion.div 
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-panel p-4 flex items-center justify-between"
          >
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{stat.label}</p>
              <div className="flex items-baseline gap-2">
                <h3 className="text-2xl font-black text-white">{stat.value}</h3>
                <span className="text-[10px] font-bold text-slate-500 uppercase">{stat.change}</span>
              </div>
            </div>
            <div className={`p-3 rounded-xl border ${stat.panelClass}`}>
              <stat.icon size={20} className={stat.iconClass} />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Header Panel */}
          <div className="glass-panel p-6 flex flex-col gap-6 relative overflow-hidden shrink-0">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 blur-[100px] rounded-full pointer-events-none"></div>
            
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="bg-blue-500/20 text-blue-400 text-xs font-bold px-2 py-1 rounded border border-blue-500/30">INTELLIGENCE REPORT</span>
                  <span className="text-slate-400 text-sm font-mono">{data.timestamp}</span>
                </div>
                <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-1">Case Analysis Summary</h1>
                <p className="text-slate-400 font-mono text-sm">CASE ID: <span className="text-slate-200">{case_id}</span></p>
              </div>
              
              <div className={`flex items-center gap-6 px-6 py-4 rounded-xl border ${riskStyle} backdrop-blur-md`}>
                <div className="flex flex-col">
                  <span className="text-xs font-bold uppercase tracking-widest opacity-80 mb-1">Risk Rating</span>
                  <span className="text-2xl font-black tracking-tight">{risk_assessment.level}</span>
                </div>
                <div className="h-12 w-px bg-current opacity-20"></div>
                <div className="flex flex-col items-end">
                  <span className="text-xs font-bold uppercase tracking-widest opacity-80 mb-1">Impact Score</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-black">{risk_assessment.score}</span>
                    <span className="opacity-60 font-bold">/100</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Inference Section */}
            <div className="border-t border-white/10 pt-4">
              {!inferenceText ? (
                <button 
                  onClick={fetchInference}
                  disabled={loadingInference}
                  className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-bold px-4 py-2 rounded-lg transition-colors shadow-[0_0_15px_rgba(147,51,234,0.3)] disabled:opacity-50"
                >
                  {loadingInference ? <Activity size={16} className="animate-spin" /> : <Zap size={16} />}
                  Draw Overall Inference
                </button>
              ) : (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4 relative">
                  <div className="flex items-center gap-2 mb-2">
                    <ShieldAlert size={16} className="text-purple-400" />
                    <h3 className="text-sm font-bold text-white tracking-widest uppercase">AI Final Inference</h3>
                  </div>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    {inferenceText}
                  </p>
                  <button onClick={() => setInferenceText(null)} className="absolute top-4 right-4 text-slate-500 hover:text-white">
                    <Activity size={14} />
                  </button>
                </motion.div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             {/* Intent Engine */}
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="glass-panel p-6 relative overflow-hidden group">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-500/20 rounded-lg border border-purple-500/30">
                    <Activity size={20} className="text-purple-400" />
                  </div>
                  <h3 className="font-display font-semibold text-white">NLP Engine Analysis</h3>
                </div>
                <span className="text-xs font-mono text-slate-500">{data.ai_metadata?.model || 'DistilBERT'}</span>
              </div>
              <div className="mb-4">
                <div className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-1">Intent Classification</div>
                <div className="text-xl font-bold text-slate-200 capitalize">{(intent.labels[0] || 'undetermined').replace('_', ' ')}</div>
              </div>
              <div className="w-full bg-slate-800/50 rounded-full h-2 mb-2 border border-white/5 overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${intent.confidence * 100}%` }} transition={{ duration: 1 }} className="bg-purple-500 h-full" />
              </div>
              <div className="text-right text-xs font-mono text-purple-400 font-bold">{(intent.confidence * 100).toFixed(1)}% CONFIDENCE</div>
            </motion.div>

            {/* Risk Factors */}
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="glass-panel p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-red-500/20 rounded-lg border border-red-500/30">
                  <ShieldAlert size={20} className="text-red-400" />
                </div>
                <h3 className="font-display font-semibold text-white">Risk Indicators</h3>
              </div>
              <div className="flex flex-col gap-3">
                {risk_assessment.reasons.slice(0, 3).map((reason: string, i: number) => (
                  <div key={i} className="flex items-start gap-3 p-2 bg-white/5 border border-white/5 rounded-lg">
                    <AlertTriangle size={14} className="text-red-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300 font-medium">{reason}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>

        {/* Sidebar Widgets */}
        <div className="flex flex-col gap-6">
          {/* Watchlist Status Panel */}
          <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="glass-panel p-5 flex flex-col h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Search size={18} className="text-blue-400" />
                <h3 className="font-display font-semibold text-white">Watchlist Status</h3>
              </div>
              <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20 uppercase font-bold">Live</span>
            </div>
            <div className="flex-1 space-y-4">
              {watchItems.length === 0 && (
                <div className="text-xs text-slate-500 bg-white/5 border border-white/5 rounded-xl p-3">
                  No backend watch entities yet. Upload evidence to populate this panel.
                </div>
              )}
              {watchItems.map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white/5 border border-white/5 rounded-xl group hover:border-white/10 transition-all cursor-pointer">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${watchDotClasses[item.color] || 'bg-slate-500'}`}></div>
                    <div>
                      <div className="text-sm font-mono text-white">{item.name}</div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest">{item.type}</div>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-slate-600 group-hover:text-white transition-colors" />
                </div>
              ))}
            </div>
            <button
              onClick={() => navigate(`/workspace/${id}/watchlist`)}
              className="mt-4 w-full bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg py-2 text-xs font-bold text-slate-400 uppercase tracking-widest transition-colors"
            >
              Manage Watchlist
            </button>
          </motion.div>

          {/* Activity Feed */}
          <div className="glass-panel p-5 flex-1">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp size={18} className="text-emerald-400" />
              <h3 className="font-display font-semibold text-white">Recent Activity</h3>
            </div>
            <div className="space-y-4">
              {[
                { msg: `${data.evidence_count || 0} evidence file(s) loaded`, time: data.timestamp?.split('T')?.[0] || 'Now', user: 'Backend Pipeline' },
                { msg: `${entityTotal} entities extracted`, time: 'Current', user: 'Entity Extractor' },
                { msg: `Risk level ${risk_assessment.level}`, time: 'Current', user: 'Risk Engine' },
              ].map((activity, i) => (
                <div key={i} className="flex gap-3 relative">
                  {i < 2 && <div className="absolute left-1.5 top-5 bottom-0 w-px bg-white/5"></div>}
                  <div className="w-3 h-3 rounded-full bg-slate-700 border border-white/10 shrink-0 mt-1"></div>
                  <div>
                    <div className="text-xs text-white font-medium">{activity.msg}</div>
                    <div className="text-[10px] text-slate-500">{activity.time} • {activity.user}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Entities & Raw Evidence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[400px]">
        {/* Extracted Entities */}
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="glass-panel p-6 flex flex-col h-full">
          <div className="flex items-center justify-between mb-6 shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
                <Fingerprint size={20} className="text-blue-400" />
              </div>
              <h3 className="font-display font-semibold text-white">Extracted Entities</h3>
            </div>
            <div className="text-xs bg-white/10 px-2 py-1 rounded text-slate-400 font-mono">
              {Object.values(entities).flat().length} FOUND
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-6">
            {Object.entries(entities).map(([type, values]: any) => {
              if (values.length === 0) return null;
              return (
                <div key={type}>
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-white/5 pb-1">{type}</div>
                  <div className="flex flex-wrap gap-2">
                    {values.map((val: string, i: number) => (
                      <div key={i} className="group relative flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-md hover:bg-blue-500/20 hover:border-blue-500/40 transition-all cursor-pointer">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 group-hover:animate-pulse"></span>
                        <span className="text-sm text-slate-200 font-mono">{val}</span>
                        <ArrowUpRight size={10} className="opacity-0 group-hover:opacity-100 transition-opacity ml-1" />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Raw Evidence */}
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="glass-panel p-6 flex flex-col h-full">
           <div className="flex items-center justify-between mb-6 shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500/20 rounded-lg border border-emerald-500/30">
                <FileText size={20} className="text-emerald-400" />
              </div>
              <h3 className="font-display font-semibold text-white">Chain of Custody Data</h3>
            </div>
            <div className="flex items-center gap-2 text-xs bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded border border-emerald-500/20 font-mono">
              <Shield size={12} /> SECURED
            </div>
          </div>
          
          <div className="flex-1 bg-[#05070a] border border-white/5 rounded-xl p-4 overflow-y-auto relative custom-scrollbar">
            <p className="font-mono text-slate-400 text-sm leading-relaxed whitespace-pre-wrap">
              {highlightTriggerWords(data.raw_text, risk_assessment.trigger_words || [])}
            </p>
          </div>
          
          <div className="mt-4 flex flex-col gap-2">
             <div className="flex items-center justify-between text-xs font-mono text-slate-500 bg-white/5 px-4 py-2 rounded-lg border border-white/5 shrink-0">
              <span className="flex items-center gap-2"><Zap size={12} className="text-yellow-500"/> SOURCE: {data.source_file || 'system_generated.log'}</span>
              <span>HASH: {(data.hashes?.[0] || data.hash || '00000000000000000000000000000000').substring(0, 24)}...</span>
            </div>
            <div className="flex items-center gap-4 text-[10px] text-slate-600 px-1">
              <span className="flex items-center gap-1"><Clock size={10}/> Updated: {data.timestamp || 'Awaiting upload'}</span>
              <span className="flex items-center gap-1"><Users size={10}/> Authenticator: Lead Investigator</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
