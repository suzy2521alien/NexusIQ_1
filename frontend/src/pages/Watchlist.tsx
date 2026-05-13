import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { emitWorkspaceRefresh, useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { Eye, Plus, Wallet, Phone, Mail, Search, Trash2, Bell, AlertCircle, CheckCircle2, MoreHorizontal, Activity } from 'lucide-react';

const Watchlist = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const refreshKey = useWorkspaceRefresh(id);
  const [activeTab, setActiveTab] = useState<'watchlist' | 'alerts'>('watchlist');
  const [showAddForm, setShowAddForm] = useState(false);
  const [watchedEntities, setWatchedEntities] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [entityType, setEntityType] = useState('Wallet');
  const [identifier, setIdentifier] = useState('');
  const [policy, setPolicy] = useState('Any Activity');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [watchlistRes, alertsRes] = await Promise.all([
          fetch(`http://localhost:8000/watchlist/list/${id}`),
          fetch(`http://localhost:8000/alerts/live/${id}`)
        ]);
        const watchlistData = await watchlistRes.json();
        const alertsData = await alertsRes.json();
        setWatchedEntities(watchlistData.entities);
        setAlerts(alertsData.alerts);
      } catch (err) {
        console.error("Failed to fetch watchlist/alerts:", err);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchData();
  }, [id, refreshKey]);

  const addEntity = async () => {
    if (!id || !identifier.trim()) return;

    setSaving(true);
    try {
      const res = await fetch('http://localhost:8000/watchlist/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: id, type: entityType, value: identifier, policy })
      });
      if (!res.ok) throw new Error('Failed to add watchlist entity');
      const data = await res.json();
      setWatchedEntities(prev => [data.entity, ...prev.filter(item => item.id !== data.entity.id)]);
      setIdentifier('');
      setShowAddForm(false);
      emitWorkspaceRefresh(id);
    } catch (err) {
      console.error("Failed to add watchlist entity:", err);
    } finally {
      setSaving(false);
    }
  };

  const removeEntity = async (entity: any) => {
    if (!id) return;

    if (!entity.id?.startsWith('MAN-')) {
      setWatchedEntities(prev => prev.filter(item => item.id !== entity.id));
      return;
    }

    try {
      await fetch(`http://localhost:8000/watchlist/${id}/${entity.id}`, { method: 'DELETE' });
      setWatchedEntities(prev => prev.filter(item => item.id !== entity.id));
      emitWorkspaceRefresh(id);
    } catch (err) {
      console.error("Failed to remove watchlist entity:", err);
    }
  };

  const markAlertReviewed = (alertId: string) => {
    setAlerts(prev => prev.map(alert => alert.id === alertId ? { ...alert, priority: 'REVIEWED', reviewed: true } : alert));
  };

  const escalateAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert => alert.id === alertId ? { ...alert, priority: 'CRITICAL', escalated: true } : alert));
  };

  if (loading) return <div className="p-8 text-slate-400 flex items-center gap-3"><Activity className="animate-spin" /> Loading monitoring data...</div>;


  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">Watchlist & Live Alerts</h1>
          <p className="text-slate-400 text-sm">Monitor specific entities across the global network and receive real-time intelligence triggers.</p>
        </div>
        <button 
          onClick={() => setShowAddForm(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 px-6 rounded-xl flex items-center gap-2 transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)]"
        >
          <Plus size={18} /> ADD TO WATCHLIST
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 p-1 rounded-xl w-fit">
        <button 
          onClick={() => setActiveTab('watchlist')}
          className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'watchlist' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
        >
          ACTIVE WATCHLIST ({watchedEntities.length})
        </button>
        <button 
          onClick={() => setActiveTab('alerts')}
          className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'alerts' ? 'bg-red-600 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
        >
          LIVE ALERTS ({alerts.length})
        </button>
      </div>

      {activeTab === 'watchlist' ? (
        <div className="glass-panel overflow-hidden flex flex-col flex-1">
          <div className="grid grid-cols-12 gap-4 p-4 border-b border-white/5 bg-white/5 text-xs font-bold text-slate-500 uppercase tracking-widest">
            <div className="col-span-1">Type</div>
            <div className="col-span-4">Entity Identifier</div>
            <div className="col-span-2">Added By</div>
            <div className="col-span-2">Added Date</div>
            <div className="col-span-2 text-center">Status</div>
            <div className="col-span-1 text-right">Actions</div>
          </div>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
            <div className="flex flex-col gap-2">
              {watchedEntities.map((entity, i) => (
                <motion.div 
                  key={entity.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="grid grid-cols-12 gap-4 p-4 bg-white/5 border border-white/5 rounded-xl items-center hover:border-white/10 transition-all group"
                >
                  <div className="col-span-1 flex justify-center">
                    {entity.type === 'Wallet' && <Wallet size={18} className="text-blue-400" />}
                    {entity.type === 'Phone' && <Phone size={18} className="text-green-400" />}
                    {entity.type === 'Email' && <Mail size={18} className="text-purple-400" />}
                  </div>
                  <div className="col-span-4 font-mono text-white">{entity.value}</div>
                  <div className="col-span-2 text-xs text-slate-400">{entity.addedBy}</div>
                  <div className="col-span-2 text-xs font-mono text-slate-500">{entity.date}</div>
                  <div className="col-span-2 flex justify-center">
                    <span className={`text-[10px] font-bold px-2 py-1 rounded border ${entity.status === 'Triggered' ? 'bg-red-500/10 text-red-400 border-red-500/30 animate-pulse' : 'bg-green-500/10 text-green-400 border-green-500/20'}`}>
                      {entity.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="col-span-1 flex justify-end gap-2">
                    <button onClick={() => navigate(`/workspace/${id}/search?q=${encodeURIComponent(entity.value)}`)} className="text-slate-600 hover:text-white transition-colors"><Search size={16} /></button>
                    <button onClick={() => removeEntity(entity)} className="text-slate-600 hover:text-red-400 transition-colors"><Trash2 size={16} /></button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-4 flex-1 overflow-y-auto custom-scrollbar pr-2">
          {alerts.map((alert, i) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`glass-panel p-6 border-l-4 ${alert.priority === 'CRITICAL' ? 'border-l-red-500 bg-red-500/5' : 'border-l-orange-500 bg-orange-500/5'}`}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${alert.priority === 'CRITICAL' ? 'bg-red-500/20' : 'bg-orange-500/20'}`}>
                    <AlertCircle size={20} className={alert.priority === 'CRITICAL' ? 'text-red-400' : 'text-orange-400'} />
                  </div>
                  <div>
                    <h3 className="font-bold text-white uppercase tracking-wider text-sm">{alert.priority} ALERT</h3>
                    <p className="text-[10px] text-slate-500 font-mono">{alert.id} • {alert.time}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => markAlertReviewed(alert.id)} className="bg-white/5 hover:bg-white/10 text-xs font-bold px-3 py-1.5 rounded-lg transition-all flex items-center gap-2">
                    <CheckCircle2 size={14} /> {alert.reviewed ? 'REVIEWED' : 'MARK REVIEWED'}
                  </button>
                  <button onClick={() => escalateAlert(alert.id)} className="bg-blue-600 hover:bg-blue-500 text-xs font-bold px-3 py-1.5 rounded-lg transition-all">
                    {alert.escalated ? 'ESCALATED' : 'ESCALATE'}
                  </button>
                </div>
              </div>
              <div className="bg-[#05070a] border border-white/5 p-4 rounded-xl">
                <div className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-1">Entity</div>
                <div className="text-blue-400 font-mono mb-3">{alert.entity}</div>
                <div className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-1">Trigger Event</div>
                <p className="text-slate-200 text-sm font-medium">{alert.trigger}</p>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Add Entity Modal (Simplified simulation) */}
      <AnimatePresence>
        {showAddForm && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 backdrop-blur-sm bg-black/60">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="glass-panel p-8 w-full max-w-md shadow-[0_0_50px_rgba(0,0,0,0.5)] border-white/10"
            >
              <h2 className="text-xl font-display font-bold text-white mb-6">Add Entity to Watchlist</h2>
              <div className="flex flex-col gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Entity Type</label>
                  <select value={entityType} onChange={(e) => setEntityType(e.target.value)} className="w-full bg-[#05070a] border border-white/10 rounded-lg py-3 px-4 text-white focus:outline-none focus:border-blue-500/50">
                    <option>Wallet</option>
                    <option>Phone</option>
                    <option>Email</option>
                    <option>IP</option>
                    <option>URL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Identifier</label>
                  <input value={identifier} onChange={(e) => setIdentifier(e.target.value)} type="text" placeholder="Enter ID..." className="w-full bg-[#05070a] border border-white/10 rounded-lg py-3 px-4 text-white focus:outline-none focus:border-blue-500/50 font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Alert Trigger Policy</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button onClick={() => setPolicy('Any Activity')} className={`${policy === 'Any Activity' ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'bg-white/5 border-white/5 text-slate-500'} border text-[10px] font-bold py-2 rounded uppercase`}>Any Activity</button>
                    <button onClick={() => setPolicy('High Velocity')} className={`${policy === 'High Velocity' ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'bg-white/5 border-white/5 text-slate-500'} border text-[10px] font-bold py-2 rounded uppercase`}>High Velocity</button>
                  </div>
                </div>
                <div className="flex gap-3 mt-4">
                  <button onClick={() => setShowAddForm(false)} className="flex-1 bg-white/5 hover:bg-white/10 py-3 rounded-lg text-sm font-bold text-white transition-all uppercase tracking-widest">Cancel</button>
                  <button onClick={addEntity} disabled={saving || !identifier.trim()} className="flex-1 bg-blue-600 hover:bg-blue-500 py-3 rounded-lg text-sm font-bold text-white transition-all uppercase tracking-widest disabled:opacity-50">{saving ? 'Saving...' : 'Confirm Monitor'}</button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Watchlist;
