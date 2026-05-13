import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { TrendingUp, AlertTriangle, ChevronRight, User, Wallet, Phone, Globe, Shield, Download, ExternalLink, Network, Activity } from 'lucide-react';

const RiskScorecard = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const refreshKey = useWorkspaceRefresh(id);
  const [selectedSuspect, setSelectedSuspect] = useState<any>(null);
  const [suspects, setSuspects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTargets = async () => {
      try {
        const res = await fetch(`http://localhost:8000/intelligence/risk-targets?case_id=${id}`);
        const data = await res.json();
        setSuspects(data.targets);
        if (data.targets.length > 0) setSelectedSuspect(data.targets[0]);
      } catch (err) {
        console.error("Failed to fetch risk targets:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchTargets();
  }, [id, refreshKey]);

  const exportRiskReport = () => {
    const payload = {
      case_id: id,
      generated_at: new Date().toISOString(),
      targets: suspects
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${id || 'case'}_risk_scorecard.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="p-8 text-slate-400 flex items-center gap-3"><Activity className="animate-spin" /> Loading risk assessments...</div>;

  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">High-Value Target Risk Scorecard</h1>
          <p className="text-slate-400 text-sm">Ranked list of entities based on ML-driven risk assessment across multiple vectors.</p>
        </div>
        <button onClick={exportRiskReport} className="bg-white/5 hover:bg-white/10 text-white text-xs font-bold px-4 py-2 rounded-lg border border-white/10 flex items-center gap-2 transition-all">
          <Download size={14} /> EXPORT FULL REPORT
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Suspect List */}
        <div className="lg:col-span-5 flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
          {suspects.map((suspect, i) => (
            <motion.div
              key={suspect.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              onClick={() => setSelectedSuspect(suspect)}
              className={`glass-panel p-5 cursor-pointer transition-all border-l-4 ${selectedSuspect?.id === suspect.id ? 'border-l-blue-500 bg-blue-500/10' : 'border-l-transparent hover:bg-white/5'}`}
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="bg-slate-800 p-3 rounded-full border border-white/10">
                    <User size={24} className={suspect.level === 'CRITICAL' ? 'text-red-500' : 'text-slate-400'} />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-lg">{suspect.name}</h3>
                    <p className="text-xs text-slate-500 font-mono uppercase tracking-widest">{suspect.alias} • {suspect.id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-black ${suspect.level === 'CRITICAL' ? 'text-red-500' : suspect.level === 'HIGH' ? 'text-orange-500' : 'text-yellow-500'}`}>
                    {suspect.score}
                  </div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">RISK SCORE</div>
                </div>
              </div>
              <div className="flex gap-4 mt-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                <span className="flex items-center gap-1"><Wallet size={12}/> {suspect.entities.wallets} Wallets</span>
                <span className="flex items-center gap-1"><Phone size={12}/> {suspect.entities.phones} Phones</span>
                <span className="flex items-center gap-1"><Shield size={12}/> {suspect.entities.cases} Cases</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Detailed Breakdown */}
        <div className="lg:col-span-7">
          {selectedSuspect ? (
            <motion.div 
              key={selectedSuspect.id}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-panel p-8 h-full flex flex-col"
            >
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h2 className="text-2xl font-display font-bold text-white mb-1">{selectedSuspect.name} Analysis</h2>
                  <p className="text-slate-400 text-sm">Full risk vector breakdown and contribution factors.</p>
                </div>
                <div className={`px-4 py-2 rounded-lg font-bold text-sm border ${selectedSuspect.level === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.3)]' : 'bg-orange-500/20 text-orange-400 border-orange-500/30'}`}>
                  {selectedSuspect.level} PRIORITY
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 flex-1">
                {selectedSuspect.factors.map((factor: any, i: number) => (
                  <div key={i} className="bg-white/5 border border-white/5 rounded-2xl p-6">
                    <div className="flex justify-between items-center mb-4">
                      <div className="flex items-center gap-3">
                        <TrendingUp size={18} className={factor.trend === 'up' ? 'text-red-400' : 'text-green-400'} />
                        <h4 className="font-bold text-white uppercase tracking-wider text-sm">{factor.label}</h4>
                      </div>
                      <div className="text-xl font-black text-blue-400">{factor.score}%</div>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 mb-4 overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${factor.score}%` }}
                        className={`h-full ${factor.score > 90 ? 'bg-red-500' : factor.score > 70 ? 'bg-orange-500' : 'bg-blue-500'}`}
                      />
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed italic">" {factor.reason} "</p>
                  </div>
                ))}
              </div>

              <div className="mt-8 pt-8 border-t border-white/5 grid grid-cols-2 gap-4">
                <button onClick={() => navigate(`/workspace/${id}/graph?focus=${encodeURIComponent(selectedSuspect.id)}`)} className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl flex justify-center items-center gap-2 transition-all">
                  <Network size={18} /> VIEW NETWORK NODE
                </button>
                <button onClick={() => navigate(`/workspace/${id}/geo?focus=${encodeURIComponent(selectedSuspect.id)}`)} className="bg-white/5 hover:bg-white/10 text-white font-bold py-3 rounded-xl flex justify-center items-center gap-2 transition-all border border-white/10">
                  <Globe size={18} /> GEOSPATIAL TRACK
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="glass-panel h-full flex flex-col items-center justify-center text-slate-600 border-dashed border-2 border-white/5">
              <AlertTriangle size={48} className="mb-4 opacity-20" />
              <p className="font-mono text-sm uppercase tracking-widest">Select a target from the list to view detailed risk breakdown.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskScorecard;
