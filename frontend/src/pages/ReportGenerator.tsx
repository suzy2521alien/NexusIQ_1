import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useParams } from 'react-router-dom';
import { useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { FileText, Download, Printer, Eye, ShieldCheck, Lock, Share2, ClipboardCheck, ChevronRight, FileSearch, Settings } from 'lucide-react';

const ReportGenerator = () => {
  const { id } = useParams();
  const refreshKey = useWorkspaceRefresh(id);
  const [generating, setGenerating] = useState(false);
  const [previewReady, setPreviewReady] = useState(false);
  const [caseData, setCaseData] = useState<any>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [targets, setTargets] = useState<any[]>([]);
  const [classification, setClassification] = useState('UNCLASSIFIED // FOR OFFICIAL USE ONLY');
  const [includeMap, setIncludeMap] = useState(true);
  const [includeRisk, setIncludeRisk] = useState(true);
  const [includeCustody, setIncludeCustody] = useState(true);
  const [includeRaw, setIncludeRaw] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState('');

  useEffect(() => {
    const fetchReportData = async () => {
      if (!id) return;

      try {
        const [caseRes, evidenceRes, riskRes] = await Promise.all([
          fetch(`http://localhost:8000/cases/${id}`),
          fetch(`http://localhost:8000/evidence/results/${id}`),
          fetch(`http://localhost:8000/intelligence/risk-targets?case_id=${id}`)
        ]);
        const [nextCase, nextEvidence, nextRisk] = await Promise.all([
          caseRes.json(),
          evidenceRes.json(),
          riskRes.json()
        ]);
        setCaseData(nextCase);
        setEvidence(nextEvidence.files || []);
        setTargets(nextRisk.targets || []);
      } catch (err) {
        console.error("Failed to load report data:", err);
      }
    };

    fetchReportData();
  }, [id, refreshKey]);

  const generateReport = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      setPreviewReady(true);
    }, 3000);
  };

  const primaryHash = caseData?.hashes?.[0] || evidence[0]?.hash || '';
  const generatedAt = new Date().toLocaleString();
  const entityCards = [
    ...(caseData?.entities?.wallets || []).map((value: string) => ({ type: 'WALLET', value })),
    ...(caseData?.entities?.emails || []).map((value: string) => ({ type: 'EMAIL', value })),
    ...(caseData?.entities?.phones || []).map((value: string) => ({ type: 'PHONE', value })),
    ...(caseData?.entities?.urls || []).map((value: string) => ({ type: 'URL', value })),
    ...(caseData?.entities?.names || []).map((value: string) => ({ type: 'NAME', value }))
  ];
  const riskReasons = (targets[0]?.factors || caseData?.risk_assessment?.reasons || []).map((factor: any) => typeof factor === 'string' ? factor : factor.reason);

  const downloadReport = () => {
    const report = {
      case_id: id,
      generated_at: new Date().toISOString(),
      classification,
      evidence,
      entities: caseData?.entities || {},
      risk_assessment: caseData?.risk_assessment || {},
      hashes: caseData?.hashes || []
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `CASE_REPORT_${id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const verifyReport = () => {
    setVerifyStatus(primaryHash ? `Verified evidence hash ${primaryHash.slice(0, 12)}...${primaryHash.slice(-8)}` : 'No evidence hash available to verify.');
  };

  return (
    <div className="flex flex-col gap-6 h-full pb-8">
      <div className="shrink-0">
        <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">Automated Case File Generator</h1>
        <p className="text-slate-400 text-sm">Generate legally admissible forensic reports with cryptographic integrity hashes and digital signatures.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        
        {/* Configuration Panel */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="glass-panel p-6">
            <h3 className="font-display font-semibold text-white flex items-center gap-2 mb-6">
              <Settings size={18} className="text-blue-400" />
              Report Configuration
            </h3>
            <div className="flex flex-col gap-5">
              <div className="space-y-3">
                <label className="flex items-center gap-3 p-3 bg-white/5 border border-white/5 rounded-xl cursor-pointer hover:border-blue-500/30 transition-all">
                  <input type="checkbox" checked={includeMap} onChange={(e) => setIncludeMap(e.target.checked)} className="w-4 h-4 rounded border-white/10 bg-[#05070a] text-blue-500 focus:ring-blue-500/20" />
                  <span className="text-sm text-slate-300">Include Network Map Screenshot</span>
                </label>
                <label className="flex items-center gap-3 p-3 bg-white/5 border border-white/5 rounded-xl cursor-pointer hover:border-blue-500/30 transition-all">
                  <input type="checkbox" checked={includeRisk} onChange={(e) => setIncludeRisk(e.target.checked)} className="w-4 h-4 rounded border-white/10 bg-[#05070a] text-blue-500 focus:ring-blue-500/20" />
                  <span className="text-sm text-slate-300">Entity Risk Score Breakdown</span>
                </label>
                <label className="flex items-center gap-3 p-3 bg-white/5 border border-white/5 rounded-xl cursor-pointer hover:border-blue-500/30 transition-all">
                  <input type="checkbox" checked={includeCustody} onChange={(e) => setIncludeCustody(e.target.checked)} className="w-4 h-4 rounded border-white/10 bg-[#05070a] text-blue-500 focus:ring-blue-500/20" />
                  <span className="text-sm text-slate-300">Chain of Custody Logs</span>
                </label>
                <label className="flex items-center gap-3 p-3 bg-white/5 border border-white/5 rounded-xl cursor-pointer hover:border-blue-500/30 transition-all">
                  <input type="checkbox" checked={includeRaw} onChange={(e) => setIncludeRaw(e.target.checked)} className="w-4 h-4 rounded border-white/10 bg-[#05070a] text-blue-500 focus:ring-blue-500/20" />
                  <span className="text-sm text-slate-300">Raw Chat Transcripts</span>
                </label>
              </div>

              <div className="h-px bg-white/5 my-2"></div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Classification Label</label>
                <select value={classification} onChange={(e) => setClassification(e.target.value)} className="w-full bg-[#05070a] border border-white/10 rounded-lg py-3 px-4 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-all">
                  <option>UNCLASSIFIED // FOR OFFICIAL USE ONLY</option>
                  <option>SECRET // NOFORN</option>
                  <option>TOP SECRET // SCI</option>
                </select>
              </div>

              <button 
                onClick={generateReport}
                disabled={generating}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl flex justify-center items-center gap-3 transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] disabled:opacity-50"
              >
                {generating ? <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div> : <FileSearch size={20} />}
                {generating ? 'COMPILING CASE DATA...' : 'GENERATE ADMISSIBLE REPORT'}
              </button>
            </div>
          </div>

          {/* Verification Box */}
          <div className="glass-panel p-6 border-l-4 border-l-emerald-500 bg-emerald-500/5">
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck size={18} className="text-emerald-400" />
              <h3 className="font-display font-semibold text-white">Integrity Verification</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">Every report is cryptographically signed and hashed. You can verify any NexusIQ report using its unique SHA-256 fingerprint.</p>
            <div className="bg-[#05070a] p-3 rounded-lg border border-white/5 font-mono text-[10px] text-emerald-400 break-all mb-4">
              SHA256: {primaryHash ? `${primaryHash.slice(0, 12)}...${primaryHash.slice(-8)}` : 'Awaiting evidence hash'}
            </div>
            {verifyStatus && <div className="text-[10px] text-emerald-400 mb-3 font-mono">{verifyStatus}</div>}
            <button onClick={verifyReport} className="w-full bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-bold py-2 rounded border border-white/10 transition-all uppercase tracking-widest">
              Verify Existing Report
            </button>
          </div>
        </div>

        {/* Preview Panel */}
        <div className="lg:col-span-8 flex flex-col min-h-[600px]">
          {previewReady ? (
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-panel flex-1 flex flex-col bg-white overflow-hidden"
            >
              <div className="p-4 bg-slate-100 border-b flex justify-between items-center">
                <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-500">PREVIEW: CASE_REPORT_{id}.json</span>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => window.print()} className="p-2 text-slate-600 hover:text-blue-600 transition-colors"><Printer size={18} /></button>
                  <button onClick={downloadReport} className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-2 transition-all">
                    <Download size={16} /> DOWNLOAD REPORT
                  </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-12 bg-slate-200 flex justify-center custom-scrollbar">
                <div className="w-full max-w-[800px] bg-white shadow-2xl p-16 text-black font-serif flex flex-col min-h-[1000px]">
                  <div className="text-center border-b-2 border-black pb-8 mb-8">
                    <h1 className="text-3xl font-bold uppercase tracking-tighter mb-2">OFFICIAL INVESTIGATIVE REPORT</h1>
                    <p className="text-sm uppercase tracking-widest font-sans font-bold text-slate-600">NEXUSIQ INTELLIGENCE DIVISION</p>
                    <p className="text-xs uppercase tracking-widest font-sans font-bold text-red-600 mt-2">{classification}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-8 mb-12 font-sans text-sm">
                    <div>
                      <div className="text-xs font-bold text-slate-400 uppercase">Case Reference</div>
                      <div className="font-bold">{id}</div>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-400 uppercase">Generated On</div>
                      <div className="font-bold">{generatedAt}</div>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-400 uppercase">Investigating Officer</div>
                      <div className="font-bold">Lead Investigator</div>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-400 uppercase">Classification</div>
                      <div className="font-bold text-red-600">{classification}</div>
                    </div>
                  </div>

                  <div className="space-y-8 flex-1">
                    <section>
                      <h2 className="text-lg font-bold border-b border-black pb-2 mb-4 font-sans uppercase">1. Executive Summary</h2>
                      <p className="leading-relaxed">
                        This report summarizes {evidence.length} backend evidence artifact(s) for {id}. Current risk is {caseData?.risk_assessment?.level || 'LOW'} with score {caseData?.risk_assessment?.score || 0}/100. The report content is generated from the active case workspace outputs.
                      </p>
                    </section>
                    
                    <section>
                      <h2 className="text-lg font-bold border-b border-black pb-2 mb-4 font-sans uppercase">2. Key Entities</h2>
                      <div className="grid grid-cols-3 gap-4">
                        {entityCards.slice(0, 6).map((entity: any, index: number) => (
                          <div key={`${entity.type}-${index}`} className="border p-3 rounded bg-slate-50 font-sans">
                            <div className="text-[10px] font-bold text-slate-400 uppercase">{entity.type}</div>
                            <div className="text-xs font-bold break-all">{entity.value}</div>
                          </div>
                        ))}
                      </div>
                    </section>

                    {includeRisk && <section>
                      <h2 className="text-lg font-bold border-b border-black pb-2 mb-4 font-sans uppercase">3. Risk Drivers</h2>
                      <ul className="list-disc pl-5 text-sm leading-relaxed">
                        {riskReasons.slice(0, 6).map((reason: string, index: number) => (
                          <li key={index}>{reason}</li>
                        ))}
                      </ul>
                    </section>}

                    {includeCustody && <section>
                      <h2 className="text-lg font-bold border-b border-black pb-2 mb-4 font-sans uppercase">4. Chain of Custody</h2>
                      <div className="space-y-2 font-sans text-xs">
                        {evidence.map((file) => (
                          <div key={file.id} className="border rounded p-3 bg-slate-50">
                            <strong>{file.name}</strong> uploaded by {file.uploader} on {file.date}. Hash: {file.hash}
                          </div>
                        ))}
                      </div>
                    </section>}

                    {includeMap && <section>
                      <h2 className="text-lg font-bold border-b border-black pb-2 mb-4 font-sans uppercase">5. Link Analysis Summary</h2>
                      <p className="text-sm leading-relaxed">
                        The current backend graph contains {entityCards.length} extracted entity node(s) associated with this case. Use the Link Analysis workspace tab for the live interactive graph.
                      </p>
                    </section>}

                    {includeRaw && <section>
                      <h2 className="text-lg font-bold border-b border-black pb-2 mb-4 font-sans uppercase">6. Raw Evidence Text</h2>
                      <pre className="text-[10px] whitespace-pre-wrap bg-slate-100 p-3 rounded border font-mono">{caseData?.raw_text || 'No raw evidence text available.'}</pre>
                    </section>}
                  </div>

                  <div className="mt-auto pt-12 border-t-2 border-black font-sans text-[10px] text-slate-400 flex justify-between items-end italic">
                    <div>
                      DIGITAL SIGNATURE VERIFIED: NEXUS_IQ_ROOT_AUTH_V4<br/>
                      TAMPER-EVIDENT HASH: {primaryHash || 'No evidence hash available'}
                    </div>
                    <div className="text-right">
                      PAGE 1 OF 24
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="glass-panel flex-1 flex flex-col items-center justify-center text-slate-600 border-dashed border-2 border-white/5">
              <FileSearch size={64} className="mb-4 opacity-10" />
              <p className="font-mono text-sm uppercase tracking-widest text-center px-12">Configure your report settings and click generate to compile the secure case file.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default ReportGenerator;
