import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams } from 'react-router-dom';
import { emitWorkspaceRefresh, useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { Users, MessageSquare, Send, Zap, Shield, Eye, Clock, Share2, AlertTriangle, Activity } from 'lucide-react';

const Collaboration = () => {
  const { id } = useParams();
  const refreshKey = useWorkspaceRefresh(id);
  const [comment, setComment] = useState('');
  const [activeUsers, setActiveUsers] = useState<any[]>([]);
  const [caseOverlap, setCaseOverlap] = useState<any[]>([]);
  const [comments, setComments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/collab/${id}/data`);
        const data = await res.json();
        setActiveUsers(data.active_users);
        setCaseOverlap(data.overlap);
        setComments(data.comments);
      } catch (err) {
        console.error("Failed to fetch collab data:", err);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchData();
  }, [id, refreshKey]);

  const sendComment = async () => {
    if (!id || !comment.trim()) return;

    setSending(true);
    try {
      const res = await fetch(`http://localhost:8000/collab/${id}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: comment, user: 'Lead Investigator' })
      });
      if (!res.ok) throw new Error('Failed to send comment');
      const data = await res.json();
      setComments(prev => [...prev, data.comment]);
      setComment('');
      setStatusMessage('Comment added to backend case thread.');
      emitWorkspaceRefresh(id);
    } catch (err) {
      console.error("Failed to send comment:", err);
      setStatusMessage('Unable to send comment.');
    } finally {
      setSending(false);
    }
  };

  const requestDeconflict = async () => {
    if (!id) return;

    try {
      const res = await fetch(`http://localhost:8000/collab/${id}/deconflict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requested_by: 'Lead Investigator' })
      });
      const data = await res.json();
      setComments(prev => [...prev, data.request]);
      setStatusMessage('De-confliction request queued.');
      emitWorkspaceRefresh(id);
    } catch (err) {
      console.error("Failed to request deconfliction:", err);
      setStatusMessage('Unable to queue de-confliction request.');
    }
  };

  const copyRoomSummary = () => {
    const summary = [
      `Case: ${id}`,
      `Active investigators: ${activeUsers.length}`,
      `Overlap alerts: ${caseOverlap.length}`,
      ...caseOverlap.map((item) => `${item.type}: ${item.entity} also in ${item.otherCase}`)
    ].join('\n');
    navigator.clipboard?.writeText(summary);
    setStatusMessage('Collaboration summary copied.');
  };

  if (loading) return <div className="p-8 text-slate-400 flex items-center gap-3"><Activity className="animate-spin" /> Syncing collaboration room...</div>;


  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      <div className="shrink-0">
        <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">Secure Collaboration Room</h1>
        <p className="text-slate-400 text-sm">Multi-agency workspace for joint investigations. Real-time presence and case overlap detection.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        
        {/* Presence & Overlap */}
        <div className="lg:col-span-4 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
          {/* Active Investigators */}
          <div className="glass-panel p-6">
            <h3 className="font-display font-semibold text-white flex items-center gap-2 mb-6">
              <Users size={18} className="text-blue-400" />
              Active Investigators
            </h3>
            <div className="flex flex-col gap-4">
              {activeUsers.map((user, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white/5 border border-white/5 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="w-10 h-10 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center font-bold text-blue-400">
                        {user.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      {user.active && <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-background"></div>}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">{user.name}</div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest">{user.agency}</div>
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-600 italic">{user.status}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Agency Overlap */}
          <div className="glass-panel p-6 border-l-4 border-l-orange-500 bg-orange-500/5">
            <h3 className="font-display font-semibold text-white flex items-center gap-2 mb-4">
              <Zap size={18} className="text-orange-400" />
              Agency Overlap Alerts
            </h3>
            <div className="flex flex-col gap-4">
              {caseOverlap.map((overlap, i) => (
                <div key={i} className="p-3 bg-white/5 border border-white/5 rounded-xl hover:border-orange-500/30 transition-all cursor-pointer">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] bg-orange-500/10 text-orange-400 px-2 py-0.5 rounded border border-orange-500/20 font-bold uppercase">{overlap.agency} MATCH</span>
                    <AlertTriangle size={14} className="text-orange-500 animate-pulse" />
                  </div>
                  <div className="text-xs font-mono text-white mb-1">{overlap.entity}</div>
                  <p className="text-[10px] text-slate-500">Found in: <span className="text-slate-300">{overlap.otherCase}</span></p>
                </div>
              ))}
              {caseOverlap.length === 0 && (
                <div className="p-3 bg-white/5 border border-white/5 rounded-xl text-xs text-slate-500">
                  No overlapping entities found in backend processed cases.
                </div>
              )}
            </div>
            <button onClick={requestDeconflict} className="mt-6 w-full bg-orange-500 hover:bg-orange-600 text-white text-xs font-bold py-2 rounded-lg transition-all uppercase tracking-widest">
              REQUEST DE-CONFLICTING
            </button>
          </div>
        </div>

        {/* Chat & Activity */}
        <div className="lg:col-span-8 glass-panel flex flex-col h-full overflow-hidden">
          <div className="p-4 border-b border-white/5 bg-white/5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MessageSquare size={18} className="text-emerald-400" />
              <h3 className="font-display font-semibold text-white">Case Discussion Thread</h3>
            </div>
            <div className="flex items-center gap-2">
              {statusMessage && <span className="text-[10px] text-blue-400 font-mono">{statusMessage}</span>}
              <button onClick={copyRoomSummary} className="p-2 text-slate-400 hover:text-white" title="Copy collaboration summary"><Share2 size={16} /></button>
              <button onClick={() => setStatusMessage(`${comments.length} comments, ${caseOverlap.length} overlap alerts loaded from backend.`)} className="p-2 text-slate-400 hover:text-white" title="Show room status"><Eye size={16} /></button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 custom-scrollbar">
            {comments.map((msg, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`flex flex-col ${msg.user === 'Lead Investigator' ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center gap-2 mb-1 px-2">
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${msg.user === 'System AI' ? 'text-blue-400' : 'text-slate-500'}`}>{msg.user}</span>
                  <span className="text-[10px] text-slate-700 font-mono">{msg.time}</span>
                </div>
                <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${msg.user === 'Lead Investigator' ? 'bg-blue-600 text-white rounded-tr-sm shadow-lg shadow-blue-600/20' : msg.user === 'System AI' ? 'bg-blue-500/10 border border-blue-500/20 text-blue-300 italic rounded-tl-sm' : 'bg-white/5 border border-white/5 text-slate-200 rounded-tl-sm'}`}>
                  {msg.text}
                </div>
              </motion.div>
            ))}
          </div>

          <div className="p-4 border-t border-white/5 bg-background">
            <div className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-xl p-2 focus-within:border-blue-500/50 transition-all">
              <input 
                type="text" 
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') sendComment();
                }}
                placeholder="Type a message or use @ to mention..." 
                className="flex-1 bg-transparent border-none outline-none text-white text-sm px-3 py-2"
              />
              <button onClick={sendComment} disabled={sending || !comment.trim()} className="bg-blue-600 hover:bg-blue-500 text-white p-2.5 rounded-lg transition-all disabled:opacity-50">
                <Send size={18} />
              </button>
            </div>
            <div className="flex gap-4 mt-2 px-2">
              <button className="text-[10px] text-slate-500 hover:text-white flex items-center gap-1 uppercase font-bold tracking-widest"><Clock size={12}/> Attach Case File</button>
              <button className="text-[10px] text-slate-500 hover:text-white flex items-center gap-1 uppercase font-bold tracking-widest"><Shield size={12}/> Secure Link</button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Collaboration;
