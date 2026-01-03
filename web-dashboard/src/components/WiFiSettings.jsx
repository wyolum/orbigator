import React, { useState, useEffect } from 'react';
import * as api from '../api';

const WiFiSettings = ({ isOpen, onClose }) => {
    const [networks, setNetworks] = useState([]);
    const [scanning, setScanning] = useState(false);
    const [ssid, setSsid] = useState('');
    const [password, setPassword] = useState('');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    useEffect(() => {
        if (isOpen) {
            handleScan();
        }
    }, [isOpen]);

    const handleScan = async () => {
        setScanning(true);
        setError(null);
        try {
            const data = await api.scanWifi();
            setNetworks(data.networks || []);
        } catch (err) {
            setError('Failed to scan for networks');
        } finally {
            setScanning(false);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        try {
            const result = await api.saveWifiConfig(ssid, password);
            setSuccess(result.message);
            // System will restart, so UI will eventually disconnect
        } catch (err) {
            setError('Failed to save WiFi configuration');
            setSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="card glass max-w-md w-full animate-fade-in">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-gradient">WiFi Configuration</h2>
                    <button onClick={onClose} className="text-dim hover:text-white">&times;</button>
                </div>

                {success ? (
                    <div className="text-center py-8">
                        <div className="text-success text-5xl mb-4">✓</div>
                        <h3 className="text-xl font-bold mb-2">Settings Saved!</h3>
                        <p className="text-dim mb-6 text-sm">
                            The Orbigator is restarting to connect to <strong>{ssid}</strong>.<br />
                            Please connect your device to the same network.
                        </p>
                        <div className="spinner mx-auto"></div>
                    </div>
                ) : (
                    <form onSubmit={handleSave}>
                        <div className="space-y-4 mb-6">
                            <div>
                                <label className="text-xs text-muted uppercase tracking-widest mb-2 block">Available Networks</label>
                                <div className="relative">
                                    <select
                                        className="w-full bg-white/5 border border-white/10 rounded-lg p-2 pr-10 text-sm focus:outline-none focus:border-primary/50 appearance-none"
                                        value={ssid}
                                        onChange={(e) => setSsid(e.target.value)}
                                        required
                                    >
                                        <option value="" disabled>Select a network...</option>
                                        {networks.map((net, i) => (
                                            <option key={i} value={net} className="bg-slate-900">{net}</option>
                                        ))}
                                    </select>
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted">
                                        ▼
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={handleScan}
                                    disabled={scanning}
                                    className="text-[10px] text-accent mt-2 hover:underline disabled:text-muted"
                                >
                                    {scanning ? 'Scanning...' : 'Refresh List'}
                                </button>
                            </div>

                            <div>
                                <label className="text-xs text-muted uppercase tracking-widest mb-2 block">Password</label>
                                <input
                                    type="password"
                                    className="w-full bg-white/5 border border-white/10 rounded-lg p-2 text-sm focus:outline-none focus:border-primary/50"
                                    placeholder="Enter password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        {error && <p className="text-danger text-xs mb-4">{error}</p>}

                        <div className="flex gap-4">
                            <button
                                type="button"
                                onClick={onClose}
                                className="btn btn-ghost flex-1"
                                disabled={saving}
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="btn btn-primary flex-1"
                                disabled={saving || !ssid}
                            >
                                {saving ? 'Saving...' : 'Connect'}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
};

export default WiFiSettings;
