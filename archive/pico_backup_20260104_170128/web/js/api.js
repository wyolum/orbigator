// Orbigator API Client
const API_BASE = '/api';

class OrbigatorAPI {
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showToast(`Error: ${error.message}`, 'danger');
            throw error;
        }
    }

    // Status
    async getStatus() {
        return this.request('/status');
    }

    // Satellites
    async getSatellites() {
        return this.request('/satellites');
    }

    async selectSatellite(satellite) {
        return this.request('/satellite', {
            method: 'POST',
            body: JSON.stringify({ satellite })
        });
    }

    async refreshTLE(satellite) {
        return this.request('/tle/refresh', {
            method: 'POST',
            body: JSON.stringify({ satellite })
        });
    }

    async setManualTLE(name, line1, line2) {
        return this.request('/tle/manual', {
            method: 'POST',
            body: JSON.stringify({ name, line1, line2 })
        });
    }

    // Mode Control
    async setMode(mode) {
        return this.request('/mode', {
            method: 'POST',
            body: JSON.stringify({ mode })
        });
    }

    // Tracking
    async setTracking(tracking) {
        return this.request('/tracking', {
            method: 'POST',
            body: JSON.stringify({ tracking })
        });
    }

    // Orbit Parameters
    async setOrbitParams(params) {
        return this.request('/orbit/params', {
            method: 'POST',
            body: JSON.stringify(params)
        });
    }

    // Motors
    async getMotors() {
        return this.request('/motors');
    }

    async nudgeMotor(motor, delta) {
        return this.request('/motors/nudge', {
            method: 'POST',
            body: JSON.stringify({ motor, delta })
        });
    }
}

// Global API instance
const api = new OrbigatorAPI();
