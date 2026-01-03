import React, { useState, useEffect } from 'react';
import { Satellite, Wifi, RefreshCw, AlertCircle, ChevronRight, Settings } from 'lucide-react';
import WiFiSettings from './components/WiFiSettings';
import SatelliteSelector from './components/SatelliteSelector';
import * as api from './api';

const App = () => {
  const [status, setStatus] = useState(null);
  const [motors, setMotors] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isWifiOpen, setIsWifiOpen] = useState(false);
  const [isSatOpen, setIsSatOpen] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [stat, mot] = await Promise.all([
          api.fetchStatus(),
          api.fetchMotors()
        ]);
        setStatus(stat);
        setMotors(mot);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setError('Pico connection lost. Retrying...');
      }
    };

    loadData();
    const interval = setInterval(loadData, 2000); // 2 second refresh
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="app-container flex items-center justify-center min-vh-100">
        <div className="text-center">
          <div className="spinner mb-4 mx-auto"></div>
          <p className="text-dim">Establishing connection to Orbigator...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-4xl font-bold mb-1">
            <span className="text-gradient">Orbigator</span> HUD
          </h1>
          <p className="text-dim mono text-xs tracking-widest uppercase">Orbital Tracking System v2.0</p>
        </div>

        <div className="flex gap-4">
          {status?.mode === 'sgp4' && (
            <button
              onClick={() => setIsSatOpen(true)}
              className="glass px-4 py-2 rounded-full flex items-center gap-2 hover:bg-white/10 transition-colors border-accent/30"
            >
              <div className="w-2 h-2 rounded-full bg-accent animate-pulse"></div>
              <span className="text-xs font-semibold mono uppercase">{status?.satellite || 'Select Sat'}</span>
            </button>
          )}
          {status?.rtc?.synced && (
            <div className="glass px-4 py-1.5 rounded-full flex items-center gap-2 border-white/5">
              <div className="w-1.5 h-1.5 rounded-full bg-success shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>
              <span className="text-[10px] font-medium text-white/50 mono uppercase tracking-wider text-nowrap">UTC Sync</span>
            </div>
          )}
          <button
            onClick={() => setIsWifiOpen(true)}
            className="glass px-4 py-2 rounded-full flex items-center gap-2 hover:bg-white/10 transition-colors"
          >
            <Wifi size={14} className={status?.wifi?.connected ? 'text-success' : 'text-white/40'} />
            <span className="text-xs font-medium text-white/50 mono uppercase">
              {status?.wifi?.connected ? status.wifi.ssid : (status?.wifi?.ssid === 'AP MODE' ? 'Setup WiFi' : 'Connect WiFi')}
            </span>
          </button>
          <div className="glass px-4 py-2 rounded-full flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${status?.rtc?.synced ? 'bg-accent' : 'bg-warning'} pulse`}></div>
            <span className="text-xs font-semibold mono uppercase">UTC Sync</span>
          </div>
        </div>
      </header>

      {/* WiFi Modal */}
      <WiFiSettings
        isOpen={isWifiOpen}
        onClose={() => setIsWifiOpen(false)}
      />
      <SatelliteSelector
        isOpen={isSatOpen}
        onClose={() => setIsSatOpen(false)}
        currentSatellite={status?.satellite}
      />

      {/* Main Dashboard - Minimalist Stats Layout */}
      <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

        {/* Latitude Card */}
        <section className="glass p-8 rounded-3xl flex flex-col justify-between relative overflow-hidden group">
          <div className="relative z-10 text-center">
            <h3 className="text-white/40 text-xs font-bold tracking-[0.2em] uppercase mb-4">Latitude</h3>
            <div className="text-5xl font-bold tracking-tighter text-white font-mono leading-none">
              {status?.position?.lat?.toFixed(2) || '0.00'}°
            </div>
            <div className="mt-4 text-[10px] text-white/20 uppercase font-bold tracking-widest">Global Y-Axis</div>
          </div>
        </section>

        {/* Longitude Card */}
        <section className="glass p-8 rounded-3xl flex flex-col justify-between relative overflow-hidden group">
          <div className="relative z-10 text-center">
            <h3 className="text-white/40 text-xs font-bold tracking-[0.2em] uppercase mb-4">Longitude</h3>
            <div className="text-5xl font-bold tracking-tighter text-white font-mono leading-none">
              {status?.position?.lon?.toFixed(2) || '0.00'}°
            </div>
            <div className="mt-4 text-[10px] text-white/20 uppercase font-bold tracking-widest">Global X-Axis</div>
          </div>
        </section>

        {/* AoV Motor Card */}
        <section className="glass p-8 rounded-3xl flex flex-col justify-between relative overflow-hidden group">
          <div className="relative z-10 text-center">
            <h3 className="text-white/40 text-xs font-bold tracking-[0.2em] uppercase mb-4">AoV Motor</h3>
            <div className="text-5xl font-bold tracking-tighter text-accent font-mono leading-none">
              {(status?.motors?.aov % 360).toFixed(1)}°
            </div>
            <div className="mt-4 text-[10px] text-white/20 uppercase font-bold tracking-widest">Inclination Drive</div>
          </div>
        </section>

        {/* EQX Motor Card */}
        <section className="glass p-8 rounded-3xl flex flex-col justify-between relative overflow-hidden group">
          <div className="relative z-10 text-center">
            <h3 className="text-white/40 text-xs font-bold tracking-[0.2em] uppercase mb-4">EQX Motor</h3>
            <div className="text-5xl font-bold tracking-tighter text-accent font-mono leading-none">
              {(status?.motors?.eqx % 360).toFixed(1)}°
            </div>
            <div className="mt-4 text-[10px] text-white/20 uppercase font-bold tracking-widest">Rotation Drive</div>
          </div>
        </section>

      </main>

      {/* Mode & Satellite Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        <section className="glass p-8 rounded-3xl">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-white/40 text-xs font-bold tracking-widest uppercase">System Mode</h3>
              <h2 className="text-2xl font-bold tracking-tight text-white uppercase">{status?.mode || 'Loading...'}</h2>
            </div>
            <button className="px-6 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-bold tracking-widest transition-all">SWITCH MODE</button>
          </div>
          <p className="text-white/40 text-sm leading-relaxed">
            Toggle between basic <span className="text-white/60">ORBIT</span> mechanics and real-time <span className="text-white/60">SGP4</span> satellite tracking.
          </p>
        </section>

        {status?.mode === 'sgp4' && (
          <section className="glass p-8 rounded-3xl relative overflow-hidden">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-white/40 text-xs font-bold tracking-widest uppercase mb-1">Active Object</h3>
                <h2 className="text-2xl font-bold tracking-tight text-white mb-2">{status?.satellite}</h2>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-success/20 text-success border border-success/20 font-bold mono">TLE: {status?.tle_age}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/40 border border-white/10 font-bold mono">ALT: {status?.position?.alt}km</span>
                </div>
              </div>
              <button
                onClick={() => setIsSatOpen(true)}
                className="p-3 bg-accent/20 text-accent rounded-2xl hover:bg-accent/30 transition-all border border-accent/30"
              >
                <Satellite size={20} />
              </button>
            </div>
          </section>
        )}
      </div>

      {/* Footer Info */}
      <footer className="mt-12 flex justify-between items-center text-muted text-xs">
        <p className="mono">SYSTEM ADDRESS: {window.location.hostname}</p>
        <p className="mono">FIRMWARE: PICO2-MP-ORB-2026.01</p>
      </footer>

      {error && (
        <div className="toast bg-danger border-none text-white font-bold">
          {error}
        </div>
      )}
    </div>
  );
};

export default App;
