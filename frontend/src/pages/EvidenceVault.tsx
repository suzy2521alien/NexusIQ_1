import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams } from 'react-router-dom';
import { emitWorkspaceRefresh, useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { 
  UploadCloud, FileText, FileImage, FileCode, CheckCircle, 
  Clock, ShieldAlert, Loader2, X, FileSearch, Database, 
  ChevronRight, ArrowUpRight, Clipboard, Trash2, AlertCircle, Search
} from 'lucide-react';

const EvidenceVault = () => {
  const { id } = useParams();
  const refreshKey = useWorkspaceRefresh(id);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [showMetadataForm, setShowMetadataForm] = useState(false);
  const [currentUpload, setCurrentUpload] = useState<any>(null);
  const [filterQuery, setFilterQuery] = useState('');
  const [deletingIds, setDeletingIds] = useState<Record<string, boolean>>({});

  // Form states for Chain of Custody
  const [caseId, setCaseId] = useState(id || '');
  const [officer, setOfficer] = useState('Lead Investigator');
  const [source, setSource] = useState('Physical Seizure');

  useEffect(() => {
    const activeCase = id || caseId;
    setCaseId(activeCase);
    setLoading(true);

    fetch(`http://localhost:8000/evidence/results/${activeCase}`)
      .then(res => res.ok ? res.json() : Promise.reject(new Error('Unable to load evidence inventory')))
      .then(data => setFiles(data.files || []))
      .catch(err => {
        console.error("Evidence inventory error:", err);
        setFiles([]);
      })
      .finally(() => setLoading(false));
  }, [id, refreshKey]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = e.dataTransfer?.files;
    if (droppedFiles && droppedFiles.length > 0) {
      initiateUpload(droppedFiles[0]);
    }
  };

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      initiateUpload(e.target.files[0]);
    }
  };

  const initiateUpload = (file: File) => {
    setSelectedFile(file);
    const fileId = `NEW-${Math.floor(Math.random() * 9000) + 1000}`;
    setCurrentUpload({ id: fileId, name: file.name, size: `${(file.size / (1024 * 1024)).toFixed(2)} MB` });
    setShowMetadataForm(true);
  };

  const confirmUpload = async () => {
    if (!currentUpload || !selectedFile) return;
    
    const formData = new FormData();
    formData.append('files', selectedFile);
    formData.append('case_id', caseId);
    formData.append('officer', officer);
    formData.append('source', source);

    const newFile = {
      ...currentUpload,
      type: currentUpload.name.split('.').pop() || 'file',
      date: new Date().toISOString().replace('T', ' ').substring(0, 16) + 'Z',
      status: 'UPLOADING',
      uploader: officer,
      caseId: caseId
    };

    setFiles([newFile, ...files]);
    setShowMetadataForm(false);

    try {
      // Simulate real-time progress for UI
      setUploadProgress(prev => ({ ...prev, [newFile.id]: 10 }));
      
      const res = await fetch('http://localhost:8000/evidence/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      
      setUploadProgress(prev => ({ ...prev, [newFile.id]: 100 }));
      setFiles(prev => prev.map(f => f.id === newFile.id ? {
        ...f,
        status: 'ANALYZED',
        id: data.evidence_id,
        hash: data.hash,
        caseId: data.case_id,
        message: data.message,
        entities: data.processed_output?.entities || {}
      } : f));
      emitWorkspaceRefresh(data.case_id || caseId);
    } catch (err) {
      console.error("Upload error:", err);
      setFiles(prev => prev.map(f => f.id === newFile.id ? { ...f, status: 'FAILED' } : f));
    }
  };

  const deleteEvidence = async (file: any) => {
    if (!file?.id || file.status === 'UPLOADING') return;

    const confirmed = window.confirm(`Delete ${file.name} from ${caseId}? This will rebuild the case graph and refresh the workspace.`);
    if (!confirmed) return;

    setDeletingIds(prev => ({ ...prev, [file.id]: true }));

    try {
      const res = await fetch(`http://localhost:8000/evidence/${caseId}/${encodeURIComponent(file.id)}`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Evidence deletion failed');
      }

      setFiles(prev => prev.filter(item => item.id !== file.id));
      emitWorkspaceRefresh(caseId);
    } catch (err) {
      console.error("Evidence delete error:", err);
      alert(err instanceof Error ? err.message : 'Evidence deletion failed');
    } finally {
      setDeletingIds(prev => {
        const next = { ...prev };
        delete next[file.id];
        return next;
      });
    }
  };

  const getFileIcon = (type: string) => {
    switch(type.toLowerCase()) {
      case 'image': case 'png': case 'jpg': return <FileImage className="text-blue-400" />;
      case 'csv': case 'xlsx': return <FileCode className="text-green-400" />;
      default: return <FileText className="text-slate-400" />;
    }
  };

  const filteredFiles = files.filter((file) => {
    const query = filterQuery.trim().toLowerCase();
    if (!query) return true;

    const entityText = Object.values(file.entities || {})
      .flat()
      .join(' ')
      .toLowerCase();
    const searchable = [
      file.name,
      file.id,
      file.type,
      file.size,
      file.date,
      file.status,
      file.uploader,
      file.hash,
      file.message,
      entityText
    ].filter(Boolean).join(' ').toLowerCase();

    return searchable.includes(query);
  });

  return (
    <div className="flex flex-col h-full gap-6 pb-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">Evidence Vault & Chain of Custody</h1>
          <p className="text-slate-400 text-sm">Secure ingest portal for all investigative artifacts. Automated NLP processing and graph integration.</p>
        </div>
        <div className="flex gap-4">
          <div className="glass-panel px-4 py-2 flex items-center gap-2">
            <Database size={16} className="text-blue-400" />
            <span className="text-xs font-mono text-slate-300">Vault Capacity: 4.2TB / 10TB</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        
        {/* Upload & Logs Column */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div 
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`glass-panel p-8 flex flex-col items-center justify-center text-center transition-all border-2 border-dashed relative overflow-hidden group ${isDragging ? 'border-blue-500 bg-blue-500/10 scale-[1.01]' : 'border-white/10 hover:border-white/20'}`}
          >
            {isDragging && <div className="absolute inset-0 bg-blue-500/5 animate-pulse pointer-events-none"></div>}
            <div className={`p-5 rounded-full mb-4 transition-all ${isDragging ? 'bg-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.5)]' : 'bg-white/5 group-hover:bg-white/10'}`}>
              <UploadCloud size={32} className={isDragging ? 'text-white' : 'text-slate-400'} />
            </div>
            <h3 className="font-display font-bold text-lg text-white mb-2">Secure Dropzone</h3>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">Drag & drop files (CSV, PDF, TXT, Logs).<br/>Maximum individual file size: 2GB.</p>
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileSelect}
              className="hidden" 
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="bg-white/5 hover:bg-white/10 text-white text-xs font-bold py-2.5 px-6 rounded-lg transition-all border border-white/10 uppercase tracking-widest"
            >
              Browse Filesystem
            </button>
          </div>

          <div className="glass-panel p-6 flex-1 flex flex-col min-h-0">
            <h3 className="font-display font-semibold text-white flex items-center gap-2 mb-6">
              <Clipboard size={18} className="text-purple-400" />
              Ingest Activity Log
            </h3>
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-4">
              {[
                { time: '21:05', user: 'Alpha', action: 'Upload Success', file: 'binance_dump.csv' },
                { time: '20:42', user: 'Vance', action: 'Chain Verified', file: 'chat_export.pdf' },
                { time: '19:15', user: 'System', action: 'Hash Match Found', file: 'wallet_db.json' },
              ].map((log, i) => (
                <div key={i} className="text-[10px] font-mono text-slate-500 border-l border-white/10 pl-3 py-1 relative">
                  <div className="absolute left-[-4.5px] top-1.5 w-2 h-2 rounded-full bg-slate-800 border border-white/20"></div>
                  <div className="flex justify-between text-slate-400 mb-0.5">
                    <span className="text-purple-400 font-bold">{log.time} UTC</span>
                    <span>@{log.user}</span>
                  </div>
                  <div className="text-white font-medium">{log.action}</div>
                  <div className="truncate text-slate-600 italic">{log.file}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Evidence List */}
        <div className="lg:col-span-8 glass-panel p-6 flex flex-col h-full overflow-hidden">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-display font-semibold text-white flex items-center gap-2">
              <FileSearch size={18} className="text-blue-400" />
              Evidence Inventory
            </h3>
            <div className="flex items-center gap-2">
               <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  placeholder="Filter artifact..."
                  className="bg-[#05070a] border border-white/10 rounded-lg py-1.5 pl-9 pr-4 text-xs text-white focus:outline-none focus:border-blue-500/50"
                />
              </div>
              {filterQuery && (
                <button onClick={() => setFilterQuery('')} className="text-[10px] text-slate-500 hover:text-white uppercase tracking-widest">
                  Clear
                </button>
              )}
            </div>
          </div>
          
          <div className="bg-[#05070a] border border-white/5 rounded-xl overflow-hidden flex-1 flex flex-col min-h-0">
            <div className="grid grid-cols-12 gap-4 p-4 border-b border-white/5 bg-white/5 text-[10px] font-bold text-slate-500 uppercase tracking-widest shrink-0">
              <div className="col-span-1 text-center">Format</div>
              <div className="col-span-4">Artifact Metadata</div>
              <div className="col-span-2">Uploader</div>
              <div className="col-span-3">Status Pipeline</div>
              <div className="col-span-2 text-right">Actions</div>
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
              <div className="flex flex-col gap-2">
                {loading && (
                  <div className="p-8 text-center text-xs text-slate-500 font-mono uppercase tracking-widest">
                    Loading backend evidence inventory...
                  </div>
                )}
                {!loading && files.length === 0 && (
                  <div className="p-8 text-center text-xs text-slate-500 font-mono uppercase tracking-widest">
                    No backend evidence found for this case yet.
                  </div>
                )}
                {!loading && files.length > 0 && filteredFiles.length === 0 && (
                  <div className="p-8 text-center text-xs text-slate-500 font-mono uppercase tracking-widest">
                    No artifacts match "{filterQuery}".
                  </div>
                )}
                {!loading && filteredFiles.map((file, idx) => (
                  <motion.div 
                    key={file.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="grid grid-cols-12 gap-4 p-3 bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 rounded-xl items-center transition-all group"
                  >
                    <div className="col-span-1 flex justify-center">
                      <div className="p-2 bg-white/5 rounded-lg group-hover:bg-blue-500/10 transition-colors">
                        {getFileIcon(file.type)}
                      </div>
                    </div>
                    <div className="col-span-4">
                      <div className="text-sm font-medium text-slate-200 group-hover:text-blue-400 transition-colors truncate">{file.name}</div>
                      <div className="text-[9px] font-mono text-slate-500 flex items-center gap-2 mt-0.5">
                        <span className="text-slate-600">ID: {file.id}</span>
                        <span className="w-1 h-1 rounded-full bg-slate-800"></span>
                        <span>{file.size}</span>
                        <span className="w-1 h-1 rounded-full bg-slate-800"></span>
                        <span className="text-blue-500/60 font-bold">{file.hash ? `${file.hash.slice(0, 12)}...` : 'HASH PENDING'}</span>
                      </div>
                      {file.message && (
                        <div className="text-[9px] text-slate-500 truncate mt-1">{file.message}</div>
                      )}
                    </div>
                    <div className="col-span-2">
                      <div className="text-xs text-slate-400">{file.uploader}</div>
                      <div className="text-[9px] text-slate-600 font-mono">{file.date}</div>
                    </div>
                    <div className="col-span-3">
                      {file.status === 'ANALYZED' ? (
                        <div className="flex items-center gap-2 text-[10px] font-bold text-green-400">
                          <CheckCircle size={12} /> COMPLETED
                          <div className="h-1 flex-1 bg-green-500/20 rounded-full overflow-hidden">
                            <div className="h-full bg-green-500 w-full"></div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col gap-1.5">
                          <div className="flex justify-between items-center text-[9px] font-bold">
                            <span className="text-blue-400 flex items-center gap-1">
                              <Loader2 size={10} className="animate-spin" /> {file.status}
                            </span>
                            <span className="text-slate-500 font-mono">{Math.floor(uploadProgress[file.id] || 0)}%</span>
                          </div>
                          <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${uploadProgress[file.id] || 0}%` }}
                              className="h-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="col-span-2 flex justify-end gap-2">
                      <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition-all"><ArrowUpRight size={14} /></button>
                      <button
                        onClick={() => deleteEvidence(file)}
                        disabled={Boolean(deletingIds[file.id]) || file.status === 'UPLOADING'}
                        className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-red-400 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {deletingIds[file.id] ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Metadata / Chain of Custody Modal */}
      <AnimatePresence>
        {showMetadataForm && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 backdrop-blur-md bg-black/70">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel p-8 w-full max-w-xl shadow-[0_0_50px_rgba(0,0,0,0.5)] border-white/10"
            >
              <div className="flex justify-between items-center mb-8">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-600 rounded-xl shadow-lg shadow-blue-600/20">
                    <ShieldAlert size={24} className="text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-display font-bold text-white">Chain of Custody Form</h2>
                    <p className="text-xs text-slate-500 uppercase tracking-widest font-bold">Forensic Ingest Phase: 01</p>
                  </div>
                </div>
                <button onClick={() => setShowMetadataForm(false)} className="text-slate-500 hover:text-white"><X size={24} /></button>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl mb-8 flex items-center gap-4">
                <FileText size={32} className="text-blue-400" />
                <div>
                  <div className="text-sm font-bold text-white">{currentUpload?.name}</div>
                  <div className="text-xs text-slate-400">{currentUpload?.size} • Ready for secure transfer</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6 mb-8">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Case ID Reference</label>
                  <input 
                    type="text" 
                    value={caseId}
                    onChange={(e) => setCaseId(e.target.value)}
                    className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all font-mono" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Handling Investigator</label>
                  <input 
                    type="text" 
                    value={officer}
                    onChange={(e) => setOfficer(e.target.value)}
                    className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all font-sans" 
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Artifact Source / Origin</label>
                  <select 
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className="w-full bg-[#05070a] border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-blue-500 transition-all appearance-none"
                  >
                    <option>Physical Seizure - Main suspect residence</option>
                    <option>Warrant Search - Google Cloud Bucket</option>
                    <option>Intercepted Communication - Telegram Export</option>
                    <option>Bank Records - SWIFT Transaction Log</option>
                  </select>
                </div>
              </div>

              <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl mb-8 flex items-start gap-3">
                <AlertCircle size={18} className="text-red-400 shrink-0 mt-0.5" />
                <p className="text-[10px] text-red-300 italic leading-relaxed">
                  I hereby certify that the information provided is true and correct to the best of my knowledge. Any tampering with digital evidence is a federal offense and will be logged with my cryptographic LEO badge signature.
                </p>
              </div>

              <div className="flex gap-4">
                <button onClick={() => setShowMetadataForm(false)} className="flex-1 bg-white/5 hover:bg-white/10 py-4 rounded-xl text-xs font-bold text-slate-400 uppercase tracking-widest transition-all">Cancel Ingest</button>
                <button onClick={confirmUpload} className="flex-1 bg-blue-600 hover:bg-blue-500 py-4 rounded-xl text-xs font-bold text-white uppercase tracking-widest transition-all shadow-lg shadow-blue-600/30">Sign & Commit to Vault</button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EvidenceVault;
