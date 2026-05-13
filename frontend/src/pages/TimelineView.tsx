import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { motion } from 'framer-motion';
import { Play, Pause, SkipBack, SkipForward, AlertTriangle, Fingerprint, Activity, FileText, Network, ShieldAlert, Loader2 } from 'lucide-react';

const TimelineView = () => {
  const { id } = useParams();
  const refreshKey = useWorkspaceRefresh(id);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(100);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const getEventIcon = (kind: string) => {
    switch (kind) {
      case 'evidence': return <FileText size={16} />;
      case 'hash': return <Fingerprint size={16} />;
      case 'entity': return <Activity size={16} />;
      case 'graph': return <Network size={16} />;
      case 'risk': return <ShieldAlert size={16} />;
      default: return <AlertTriangle size={16} />;
    }
  };

  const formatEventDate = (timestamp: string) => {
    if (!timestamp) return 'N/A';
    return timestamp.replace('T', ' ').substring(0, 17) + 'Z';
  };

  useEffect(() => {
    const fetchTimelineData = async () => {
      try {
        setLoading(true);
        const res = await fetch(`http://localhost:8000/graph/timeline/${id}`);
        const data = await res.json();
        setEvents(data.events || []);
      } catch (err) {
        console.error("Timeline data error", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTimelineData();
  }, [id, refreshKey]);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      if (progress >= 100) setProgress(0);
      interval = setInterval(() => {
        setProgress(p => {
          if (p >= 100) {
            setIsPlaying(false);
            return 100;
          }
          return p + 0.5;
        });
      }, 50);
    }
    return () => clearInterval(interval);
  }, [isPlaying, progress]);

  const visibleEvents = events.length > 0 ? Math.floor((progress / 100) * events.length) : 0;

  return (
    <div className="flex flex-col h-full gap-6 pb-8">
      <div className="shrink-0 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">Temporal Analysis Replay</h1>
          <p className="text-slate-400 text-sm">Time Machine: replay backend evidence ingestion, entity extraction, graph updates, and risk scoring for {id}.</p>
        </div>
        
        {/* Controls */}
        <div className="glass-panel flex items-center gap-4 px-6 py-3 rounded-full">
          <button className="text-slate-400 hover:text-white transition-colors" onClick={() => setProgress(0)}>
            <SkipBack size={20} />
          </button>
          <button 
            className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition-colors shadow-[0_0_15px_rgba(59,130,246,0.5)]"
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <Pause size={20} /> : <Play size={20} className="ml-1" />}
          </button>
          <button className="text-slate-400 hover:text-white transition-colors" onClick={() => setProgress(100)}>
            <SkipForward size={20} />
          </button>
          <div className="w-px h-6 bg-white/10 mx-2"></div>
          <div className="text-xs font-mono text-blue-400 font-bold">{Math.round(progress)}% TIMELINE</div>
        </div>
      </div>

      <div className="glass-panel flex-1 relative overflow-hidden flex flex-col p-8">
        
        {/* Progress Bar */}
        <div className="w-full h-1 bg-white/5 rounded-full mb-12 relative overflow-hidden shrink-0">
          <motion.div 
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-600 to-blue-400"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Timeline Path */}
        <div className="relative flex-1 overflow-y-auto custom-scrollbar pl-8">
          <div className="absolute left-[39px] top-0 bottom-0 w-0.5 bg-white/5"></div>
          <motion.div 
            className="absolute left-[39px] top-0 bottom-0 w-0.5 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)] origin-top"
            style={{ scaleY: progress / 100 }}
          />

          <div className="flex flex-col gap-10 relative z-10 pb-8">
            {!loading && events.length === 0 && (
              <div className="p-8 text-center text-xs text-slate-500 font-mono uppercase tracking-widest">
                No backend timeline events found for this case yet. Upload evidence to create the first event.
              </div>
            )}
            {events.map((event, idx) => {
              const isVisible = idx <= visibleEvents || progress === 100;
              const date = formatEventDate(event.timestamp);
              
              return (
                <motion.div 
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: isVisible ? 1 : 0.2, x: isVisible ? 0 : -20, filter: isVisible ? 'blur(0px)' : 'blur(4px)' }}
                  transition={{ duration: 0.4 }}
                  className="flex gap-8 items-start group"
                >
                  <div className="flex flex-col items-end w-32 shrink-0 pt-1">
                    <span className="text-xs font-mono text-slate-500 group-hover:text-slate-300 transition-colors">{date.split(' ')[0]}</span>
                    <span className="text-[10px] font-mono text-slate-600">{date.split(' ')[1]}</span>
                  </div>
                  
                  <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center shrink-0 z-10 bg-background transition-colors ${isVisible ? (event.alert ? 'border-red-500 text-red-500 shadow-[0_0_15px_rgba(239,68,68,0.4)]' : 'border-blue-500 text-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.4)]') : 'border-white/10 text-slate-600'}`}>
                    {getEventIcon(event.kind)}
                  </div>
                  
                  <div className={`flex-1 p-4 rounded-xl border transition-all ${isVisible ? (event.alert ? 'bg-red-500/5 border-red-500/20' : 'bg-white/5 border-white/10') : 'bg-transparent border-transparent'}`}>
                    <div className={`text-xs font-bold uppercase tracking-widest mb-1 ${isVisible ? (event.alert ? 'text-red-400' : 'text-blue-400') : 'text-slate-600'}`}>
                      {event.type}
                    </div>
                    <div className={`text-sm ${isVisible ? 'text-slate-200' : 'text-slate-600'}`}>
                      {event.desc}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimelineView;
