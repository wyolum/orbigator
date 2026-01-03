import React, { useState, useEffect } from 'react';
import { Rocket, Satellite, RefreshCw, X, ChevronRight, Check } from 'lucide-react';
import * as api from '../api';

const SatelliteSelector = ({ isOpen, onClose, currentSatellite }) => {
    const [satellites, setSatellites] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selecting, setSelecting] = useState(null);

    useEffect(() => {
        if (isOpen) {
            loadSatellites();
        }
    }, [isOpen]);

    const loadSatellites = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await api.fetchSatellites();
            setSatellites(data.satellites || []);
        } catch (err) {
            setError('Failed to fetch satellite catalog');
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = async (name) => {
        setSelecting(name);
        try {
            await api.selectSatellite(name);
            onClose();
        } catch (err) {
            setError(`Failed to select ${name}`);
        } finally {
            setSelecting(null);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="glass w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="flex items-center justify-between p-6 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-accent/20 text-accent">
                            <Satellite size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold tracking-tight text-white">Select Satellite</h2>
                            <p className="text-xs text-white/40 uppercase tracking-widest font-semibold mono">ORBITAL CATALOG</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/10 rounded-full transition-colors text-white/60"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="p-4 max-h-[60vh] overflow-y-auto">
                    {error && (
                        <div className="mb-4 p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm flex gap-3">
                            <X size={16} className="shrink-0" />
                            {error}
                        </div>
                    )}

                    <div className="space-y-2">
                        {satellites.map((sat) => (
                            <button
                                key={sat.name}
                                onClick={() => handleSelect(sat.name)}
                                disabled={selecting !== null}
                                className={`w-full group flex items-center justify-between p-4 rounded-xl border transition-all duration-200 ${currentSatellite === sat.name
                                        ? 'bg-accent/20 border-accent/40 text-white'
                                        : 'bg-white/5 border-white/10 hover:bg-white/10 text-white/70 hover:text-white'
                                    }`}
                            >
                                <div className="flex items-center gap-4">
                                    <div className={`p-2 rounded-lg ${currentSatellite === sat.name ? 'bg-accent/40 text-white' : 'bg-white/10 text-white/40 group-hover:text-white/60'}`}>
                                        <Rocket size={18} />
                                    </div>
                                    <div className="text-left">
                                        <div className="font-bold tracking-wide">{sat.name}</div>
                                        <div className="text-[10px] text-white/30 font-mono">NORAD ID: {sat.norad_id}</div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3">
                                    {sat.has_tle ? (
                                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-success/20 text-success border border-success/20 font-mono uppercase">
                                            TLE OK
                                        </span>
                                    ) : (
                                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-warning/20 text-warning border border-warning/20 font-mono uppercase">
                                            NO TLE
                                        </span>
                                    )}

                                    {currentSatellite === sat.name ? (
                                        <Check size={18} className="text-accent" />
                                    ) : (
                                        <ChevronRight size={18} className="text-white/20 group-hover:text-white/60 transition-transform group-hover:translate-x-1" />
                                    )}
                                </div>
                            </button>
                        ))}

                        {loading && (
                            <div className="flex flex-col items-center justify-center p-12 text-white/40 gap-4">
                                <RefreshCw size={24} className="animate-spin" />
                                <span className="text-xs uppercase tracking-[0.2em] font-bold">Querying Catalog...</span>
                            </div>
                        )}

                        {!loading && satellites.length === 0 && !error && (
                            <div className="text-center p-8 text-white/40">
                                <p>No satellites found in catalog.</p>
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-6 bg-white/5 border-t border-white/10 flex justify-between items-center text-[10px] text-white/30 uppercase tracking-widest font-bold">
                    <span>{satellites.length} OBJECTS TRACKED</span>
                    <button
                        onClick={loadSatellites}
                        className="flex items-center gap-2 hover:text-white/60 transition-colors"
                    >
                        <RefreshCw size={12} />
                        REFRESH LIST
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SatelliteSelector;
