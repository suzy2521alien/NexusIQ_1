import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, Database, Download, Key, Lock, Search, Server,
  ShieldCheck, Terminal, Globe
} from 'lucide-react';

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState<'audit' | 'system'>('audit');
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/admin/audit-log');
      const data = await res.json();
      setAuditLogs(data.logs || []);
    } catch (err) {
      console.error("Failed to fetch audit logs:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/admin/system-health');
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      console.error("Failed to fetch system health:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'audit') fetchLogs();
    if (activeTab === 'system') fetchHealth();
  }, [activeTab]);

  const filteredLogs = auditLogs.filter((log) => {
    const needle = query.toLowerCase();
    if (!needle) return true;
    return [log.time, log.user, log.action, log.detail, log.severity]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
      .includes(needle);
  });

  const exportLogs = () => {
    const rows = [['time', 'user', 'action', 'detail', 'severity'], ...filteredLogs.map(log => [
      log.time, log.user, log.action, log.detail, log.severity
    ])];
    const csv = rows.map(row => row.map(cell => `"${String(cell || '').replaceAll('"', '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'nexusiq_audit_logs.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const statusClass = (status?: string) => (
    status?.startsWith('Online') ? 'text-green-500' : 'text-orange-400'
  );

  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      <div className="shrink-0">
        <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">System Admin Control Center</h1>
        <p className="text-slate-400 text-sm">Review backend audit activity and monitor platform health.</p>
      </div>

      <div className="flex gap-1 bg-white/5 p-1 rounded-xl w-fit">
        {[
          { id: 'audit', label: 'AUDIT LOGS', icon: Activity },
          { id: 'system', label: 'SYSTEM HEALTH', icon: Server },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-6 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === tab.id ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        {activeTab === 'audit' && (
          <div className="flex flex-col gap-4 flex-1">
            <div className="glass-panel p-4 flex flex-col md:flex-row gap-4 md:items-center md:justify-between">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Backend Audit Trail</h3>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Filter logs..."
                    className="bg-[#05070a] border border-white/10 rounded-lg py-2 pl-9 pr-4 text-xs text-white focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <button onClick={fetchLogs} className="text-xs text-slate-300 hover:text-white bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                  Refresh
                </button>
                <button onClick={exportLogs} className="text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 border border-blue-500/20 rounded-lg px-3 py-2 flex items-center gap-2">
                  <Download size={14} /> Export CSV
                </button>
              </div>
            </div>

            <div className="glass-panel flex-1 overflow-hidden flex flex-col">
              <div className="grid grid-cols-12 gap-4 p-4 border-b border-white/5 bg-white/5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                <div className="col-span-2">Timestamp</div>
                <div className="col-span-2">Actor</div>
                <div className="col-span-2">Action</div>
                <div className="col-span-4">Detail</div>
                <div className="col-span-2 text-right">Severity</div>
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
                {loading && <div className="p-8 text-center text-xs text-slate-500 font-mono uppercase">Loading audit logs...</div>}
                {!loading && filteredLogs.length === 0 && <div className="p-8 text-center text-xs text-slate-500 font-mono uppercase">No matching audit logs.</div>}
                <div className="flex flex-col gap-2">
                  {filteredLogs.map((log, i) => (
                    <div key={`${log.time}-${i}`} className="grid grid-cols-12 gap-4 p-4 border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                      <div className="col-span-2 text-[10px] font-mono text-slate-500">{log.time || 'N/A'}</div>
                      <div className="col-span-2 text-xs font-bold text-slate-300">{log.user}</div>
                      <div className="col-span-2">
                        <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">{log.action}</span>
                      </div>
                      <div className="col-span-4 text-xs text-slate-400 italic">{log.detail}</div>
                      <div className="col-span-2 text-right">
                        <span className={`text-[9px] font-black px-1.5 py-0.5 rounded ${log.severity === 'HIGH' ? 'bg-red-600 text-white' : log.severity === 'MEDIUM' ? 'bg-orange-500 text-white' : 'bg-slate-700 text-slate-300'}`}>
                          {log.severity}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'system' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="glass-panel p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <Database size={20} className="text-blue-400" />
                </div>
                <h3 className="font-display font-bold text-white">Database Status</h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Neo4j Graph Engine</span>
                  <span className={`text-[10px] font-bold uppercase ${statusClass(health?.database?.neo4j)}`}>{health?.database?.neo4j || 'Checking...'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Processed Cases</span>
                  <span className="text-xs font-mono text-white">{health?.database?.processed_cases ?? '-'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Evidence Files</span>
                  <span className="text-xs font-mono text-white">{health?.database?.evidence_files ?? '-'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Entity Nodes</span>
                  <span className="text-xs font-mono text-white">{health?.database?.entity_nodes ?? '-'}</span>
                </div>
              </div>
            </div>

            <div className="glass-panel p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
                  <Terminal size={20} className="text-purple-400" />
                </div>
                <h3 className="font-display font-bold text-white">API & Pipeline</h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">FastAPI Status</span>
                  <span className="text-[10px] font-bold text-green-500 uppercase">{health?.api?.status || 'Checking...'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Pipeline Results</span>
                  <span className="text-xs font-mono text-white">{health?.api?.pipeline_results ?? '-'}</span>
                </div>
                <div className="h-px bg-white/5"></div>
                {Object.entries(health?.api?.routes || {}).map(([name, route]) => (
                  <div key={name} className="flex justify-between gap-4">
                    <span className="text-[10px] text-slate-500 uppercase">{name}</span>
                    <span className="text-[10px] font-mono text-slate-300 truncate">{String(route)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel p-6 border-l-4 border-l-green-500">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-green-500/10 rounded-lg border border-green-500/20">
                  <ShieldCheck size={20} className="text-green-400" />
                </div>
                <h3 className="font-display font-bold text-white">Security Posture</h3>
              </div>
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <Lock size={12} className="text-green-500" /> {health?.security?.storage_hashing || 'SHA-256'} Evidence Hashing
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <Key size={12} className="text-green-500" /> {health?.security?.auth_mode || 'Single investigator login'}
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <Globe size={12} className="text-green-500" /> Chain of Custody: {health?.security?.chain_of_custody || 'Enabled'}
                </div>
              </div>
              <button onClick={fetchHealth} className="mt-6 w-full bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-bold py-2 rounded border border-white/10 transition-all uppercase tracking-widest">
                Refresh Health
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
