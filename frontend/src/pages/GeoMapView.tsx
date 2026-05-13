import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useWorkspaceRefresh } from '../hooks/useWorkspaceRefresh';
import { Crosshair, Navigation, Signal, Loader2 } from 'lucide-react';
import { ComposableMap, Geographies, Geography, Marker, Line } from 'react-simple-maps';

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const GeoMapView = () => {
  const { id } = useParams();
  const refreshKey = useWorkspaceRefresh(id);
  const [locations, setLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [targetLock, setTargetLock] = useState<string | null>(null);

  useEffect(() => {
    const fetchGeoData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/graph/${id}/geo`);
        const data = await res.json();
        if (data.status === 'success' && data.data) {
          setLocations(data.data);
        }
      } catch (err) {
        console.error("Failed to fetch geo data:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchGeoData();
  }, [id, refreshKey]);

  const handleReset = () => {
    setTargetLock(null);
  };

  const handleLockThreat = () => {
    const critical = locations.find(l => l.threat_level === 'CRITICAL');
    if (critical) {
      setTargetLock(critical.id);
    }
  };

  return (
    <div className="flex flex-col h-full gap-6 pb-8">
      <div className="shrink-0 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight mb-2">Geospatial Intelligence</h1>
          <p className="text-slate-400 text-sm">Mapping IP addresses and entity locations for {id}.</p>
        </div>
        <div className="flex gap-4">
          <div className="glass-panel px-4 py-2 flex items-center gap-3 shadow-lg">
            <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]"></div>
            <span className="text-xs font-bold text-slate-300 uppercase tracking-widest">Critical Hotspot</span>
          </div>
          <div className="glass-panel px-4 py-2 flex items-center gap-3 shadow-lg">
            <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
            <span className="text-xs font-bold text-slate-300 uppercase tracking-widest">Active Node</span>
          </div>
        </div>
      </div>

      <div className="glass-panel flex-1 relative overflow-hidden bg-[#020408]">
        {/* Overlay controls */}
        <div className="absolute top-6 left-6 z-20 flex flex-col gap-3">
          <button 
            onClick={handleReset}
            title="Reset Targets"
            className="bg-[#05070a]/90 backdrop-blur-md border border-white/10 hover:bg-white/5 transition-colors rounded-lg p-3 shadow-xl text-slate-300 hover:text-white"
          >
            <Navigation size={18} />
          </button>
          <button 
            onClick={handleLockThreat}
            title="Lock on Highest Threat"
            className="bg-[#05070a]/90 backdrop-blur-md border border-white/10 hover:bg-white/5 transition-colors rounded-lg p-3 shadow-xl text-slate-300 hover:text-white"
          >
            <Crosshair size={18} />
          </button>
          <button 
            title="Live Interpol Feed: Active"
            className="bg-[#05070a]/90 backdrop-blur-md border border-white/10 hover:bg-white/5 transition-colors rounded-lg p-3 shadow-xl text-blue-400 hover:text-blue-300 relative cursor-default"
          >
            <Signal size={18} />
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
          </button>
        </div>

        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 z-20">
            <Loader2 className="animate-spin text-blue-500" size={40} />
            <div className="font-mono text-sm text-blue-400 tracking-widest">RESOLVING GEO-IP COORDINATES...</div>
          </div>
        ) : (
          <ComposableMap
            projectionConfig={{ scale: 140 }}
            style={{ width: "100%", height: "100%" }}
          >
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill="rgba(30, 41, 59, 0.4)"
                    stroke="rgba(148, 163, 184, 0.2)"
                    strokeWidth={0.5}
                    style={{
                      default: { outline: "none" },
                      hover: { fill: "rgba(51, 65, 85, 0.6)", outline: "none" },
                      pressed: { outline: "none" },
                    }}
                  />
                ))
              }
            </Geographies>

            {/* Draw connection lines from a central point (mocking flow of funds/data) */}
            {locations.length > 0 && locations.map((loc, idx) => {
              // Draw line from the first location to all others to simulate network
              if (idx === 0) return null;
              return (
                <Line
                  key={`line-${idx}`}
                  from={[locations[0].lng, locations[0].lat]}
                  to={[loc.lng, loc.lat]}
                  stroke={targetLock === loc.id ? "rgba(239, 68, 68, 0.6)" : "rgba(59, 130, 246, 0.2)"}
                  strokeWidth={targetLock === loc.id ? 2 : 1}
                  strokeLinecap="round"
                  className={targetLock === loc.id ? "animate-pulse" : ""}
                />
              )
            })}

            {locations.map((loc, idx) => {
              const isLocked = targetLock === loc.id;
              
              return (
                <Marker key={`${loc.id}-${idx}`} coordinates={[loc.lng, loc.lat]}>
                  <g className="group cursor-pointer">
                    {/* Targeting Crosshair */}
                    {isLocked && (
                      <g>
                        <circle r={24} fill="none" stroke="#ef4444" strokeWidth="1" strokeDasharray="4 2" className="animate-[spin_4s_linear_infinite]" />
                        <circle r={30} fill="none" stroke="rgba(239, 68, 68, 0.3)" strokeWidth="0.5" />
                        <line x1="-35" y1="0" x2="-15" y2="0" stroke="#ef4444" strokeWidth="1" />
                        <line x1="15" y1="0" x2="35" y2="0" stroke="#ef4444" strokeWidth="1" />
                        <line x1="0" y1="-35" x2="0" y2="-15" stroke="#ef4444" strokeWidth="1" />
                        <line x1="0" y1="15" x2="0" y2="35" stroke="#ef4444" strokeWidth="1" />
                      </g>
                    )}
                    
                    {/* Ping Animation */}
                    <circle 
                      r={loc.threat_level === 'CRITICAL' ? (isLocked ? 16 : 12) : 8} 
                      fill={loc.threat_level === 'CRITICAL' ? "rgba(239, 68, 68, 0.3)" : "rgba(59, 130, 246, 0.3)"} 
                      className="animate-ping origin-center"
                    />
                    {/* Core Dot */}
                    <circle 
                      r={loc.threat_level === 'CRITICAL' ? 4 : 3} 
                      fill={loc.threat_level === 'CRITICAL' ? "#ef4444" : "#3b82f6"} 
                      stroke="#ffffff"
                      strokeWidth={1}
                    />
                    
                    {/* Tooltip on Hover or Lock */}
                    <g className={`transition-opacity ${isLocked ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                      <rect x="-60" y="-45" width="120" height="35" rx="4" fill="rgba(5, 7, 10, 0.9)" stroke={isLocked ? "#ef4444" : "rgba(255,255,255,0.1)"} />
                      <text textAnchor="middle" y="-30" fill="#fff" fontSize="8" fontFamily="monospace" fontWeight="bold">
                        {loc.type}: {loc.value}
                      </text>
                      <text textAnchor="middle" y="-18" fill={loc.threat_level === 'CRITICAL' ? "#fca5a5" : "#93c5fd"} fontSize="7" fontFamily="monospace">
                        {isLocked ? `TARGET LOCKED: ${loc.location_name}` : loc.location_name}
                      </text>
                    </g>
                  </g>
                </Marker>
              );
            })}
          </ComposableMap>
        )}
      </div>
    </div>
  );
};

export default GeoMapView;
