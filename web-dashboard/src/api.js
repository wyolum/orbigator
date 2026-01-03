const API_BASE = window.location.origin;

export const fetchStatus = async () => {
    const response = await fetch(`${API_BASE}/api/status`);
    if (!response.ok) throw new Error('Failed to fetch status');
    return response.json();
};

export const fetchMotors = async () => {
    const response = await fetch(`${API_BASE}/api/motors`);
    if (!response.ok) throw new Error('Failed to fetch motors');
    return response.json();
};

export const switchMode = async (mode) => {
    const response = await fetch(`${API_BASE}/api/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
    });
    if (!response.ok) throw new Error('Failed to switch mode');
    return response.json();
};

export const nudgeMotor = async (motor, delta) => {
    const response = await fetch(`${API_BASE}/api/motors/nudge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ motor, delta })
    });
    if (!response.ok) throw new Error('Failed to nudge motor');
    return response.json();
};

export const fetchSatellites = async () => {
    const response = await fetch(`${API_BASE}/api/satellites`);
    if (!response.ok) throw new Error('Failed to fetch satellites');
    return response.json();
};

export const scanWifi = async () => {
    const response = await fetch(`${API_BASE}/api/wifi/scan`);
    if (!response.ok) throw new Error('Failed to scan WiFi');
    return response.json();
};

export const saveWifiConfig = async (ssid, password) => {
    const response = await fetch(`${API_BASE}/api/wifi/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ssid, password })
    });
    if (!response.ok) throw new Error('Failed to save WiFi config');
    return response.json();
};


export const selectSatellite = async (satellite) => {
    const response = await fetch(`${API_BASE}/api/satellite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ satellite })
    });
    if (!response.ok) throw new Error('Failed to select satellite');
    return response.json();
};

export const toggleTracking = async (tracking) => {
    const response = await fetch(`${API_BASE}/api/tracking`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tracking })
    });
    if (!response.ok) throw new Error('Failed to toggle tracking');
    return response.json();
};
