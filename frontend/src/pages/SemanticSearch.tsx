import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Search, Terminal, Filter, Calendar, Tag, Share2, Bookmark, Network, Eye } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
const SemanticSearch = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [mode, setMode] = useState('all');
  const [saved, setSaved] = useState<string[]>([]);

  const queryHints: Record<string, string> = {
    all: 'find crypto wallet urgency and phishing language',
    romance: 'romance scam doctor love school fees',
    crypto: 'funds cold storage btc wallet transfer',
    phishing: 'login account frozen security portal',
    contact: 'emails phones whatsapp proton gmail'
  };

  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery) {
      setQuery(urlQuery);
    }
  }, [searchParams]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      const res = await fetch('http://localhost:8000/intelligence/semantic-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: mode === 'all' ? query : `${mode} ${query}`, case_id: id })
      });
      const data = await res.json();
      setResults(data.results);
    } catch (err) {
      console.error("Semantic search failed:", err);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      <div className="shrink-0">
        <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">Semantic Intelligence Search</h1>
        <p className="text-slate-400 text-sm">Query the entire evidence pool using natural language. The engine detects intent and coded language.</p>
      </div>

      <div className="glass-panel p-8">
        <form onSubmit={handleSearch} className="relative flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={`e.g. "${queryHints[mode]}"`}
              className="w-full bg-[#05070a] border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all font-sans text-lg placeholder-slate-700"
            />
          </div>
          <button 
            type="submit"
            disabled={isSearching}
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 px-8 rounded-xl transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] disabled:opacity-50"
          >
            {isSearching ? <Terminal className="animate-spin" /> : 'EXECUTE QUERY'}
          </button>
        </form>

        <div className="flex items-center gap-4 mt-6 text-xs text-slate-500 font-mono">
          <span className="flex items-center gap-1"><Filter size={14} /> NLP MODE:</span>
          {['all', 'romance', 'crypto', 'phishing', 'contact'].map(item => (
            <button key={item} onClick={() => setMode(item)} className={`${mode === item ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'bg-white/5 border-white/5 text-slate-400'} px-3 py-1 rounded border hover:border-white/10 capitalize`}>
              {item}
            </button>
          ))}
          <div className="flex-1"></div>
          <button onClick={() => { setMode('all'); setQuery(''); setResults([]); }} className="text-blue-400 hover:underline">Clear all filters</button>
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-4">
        {isSearching && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
            <p className="text-slate-500 font-mono text-sm animate-pulse">Running forensic NLP over backend evidence for {id}...</p>
          </div>
        )}

        <AnimatePresence>
          {results.map((result, i) => (
            <motion.div
              key={result.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-panel p-6 hover:border-blue-500/30 transition-all group"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-display font-bold text-white group-hover:text-blue-400 transition-colors">{result.title}</h3>
                    <span className="bg-blue-500/10 text-blue-400 text-[10px] font-bold px-2 py-0.5 rounded border border-blue-500/20 uppercase">
                      Score: {(result.relevance * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1"><Calendar size={12} /> {result.date}</span>
                    <span className="flex items-center gap-1"><Tag size={12} /> {result.case}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => setSaved(prev => prev.includes(result.id) ? prev.filter(item => item !== result.id) : [...prev, result.id])} title="Save result" className={`p-2 bg-white/5 rounded-lg hover:bg-white/10 transition-all ${saved.includes(result.id) ? 'text-blue-400' : 'text-slate-400 hover:text-white'}`}><Bookmark size={16} /></button>
                  <button onClick={() => navigate(`/workspace/${id}/graph`)} title="Open graph" className="p-2 bg-white/5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-all"><Network size={16} /></button>
                  <button onClick={() => navigator.clipboard?.writeText(`${result.title}\n${result.case}\n${result.snippet.replace(/<[^>]+>/g, '')}`)} title="Copy result" className="p-2 bg-white/5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-all"><Share2 size={16} /></button>
                </div>
              </div>

              <div className="bg-[#05070a] border border-white/5 p-4 rounded-xl mb-4">
                <p className="text-slate-300 italic text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: result.snippet }}></p>
              </div>

              <div className="flex flex-wrap gap-2">
                {(result.signals || []).map((signal: string) => (
                  <span key={signal} className="bg-emerald-500/10 text-emerald-400 text-[10px] font-mono px-2 py-1 rounded border border-emerald-500/20">
                    Signal: {signal}
                  </span>
                ))}
                {(result.matched_terms || []).map((term: string) => (
                  <span key={term} className="bg-purple-500/10 text-purple-400 text-[10px] font-mono px-2 py-1 rounded border border-purple-500/20">
                    Match: {term}
                  </span>
                ))}
                {result.entities.map((ent: string, idx: number) => (
                  <span key={idx} className="bg-blue-500/10 text-blue-400 text-[10px] font-mono px-2 py-1 rounded border border-blue-500/20">
                    {ent}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {!isSearching && results.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-600">
            <Search size={48} className="mb-4 opacity-20" />
            <p className="font-mono text-sm uppercase tracking-widest">No results found. Try adjusting your query or filters.</p>
            <button onClick={() => setQuery(queryHints[mode])} className="mt-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg px-4 py-2 text-xs font-bold text-slate-400 uppercase tracking-widest">
              <Eye size={14} className="inline mr-2" /> Use suggested query
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SemanticSearch;
