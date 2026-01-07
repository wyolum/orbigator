// SGP4 Satellite Tracking Logic

let satellites = [];
let selectedSatellite = null;
let statusPoller = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadSatellites();
    updateStatus();
    statusPoller = new Poller(updateStatus, 60000);
    statusPoller.start();
});

// Load Satellites
async function loadSatellites() {
    try {
        const data = await api.getSatellites();
        satellites = data.satellites || [];
        renderSatellites();
    } catch (error) {
        showToast('Failed to load satellites', 'danger');
    }
}

// Render Satellites
function renderSatellites() {
    const container = document.getElementById('satellite-list');
    const searchTerm = document.getElementById('search-input').value.toLowerCase();

    const filtered = satellites.filter(sat =>
        sat.name.toLowerCase().includes(searchTerm)
    );

    if (filtered.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No satellites found</p>';
        return;
    }

    container.innerHTML = filtered.map(sat => `
    <div class="satellite-card ${selectedSatellite === sat.name ? 'active' : ''}" onclick="selectSatellite('${sat.name}')">
      <div class="satellite-name">${sat.name}</div>
      <div class="satellite-info">
        <div>NORAD ID: ${sat.norad_id}</div>
        <div>TLE Age: <span class="badge ${getTLEBadgeClass(sat.tle_age)}">${sat.tle_age}</span></div>
        ${!sat.has_tle ? '<div class="text-warning">⚠️ No TLE data</div>' : ''}
      </div>
    </div>
  `).join('');
}

// Filter Satellites
function filterSatellites() {
    renderSatellites();
}

// Get TLE Badge Class
function getTLEBadgeClass(age) {
    if (age === 'none') return 'badge-danger';
    if (age.includes('h') || age === '0m') return 'badge-success';
    if (age.includes('d')) {
        const days = parseInt(age);
        return days > 7 ? 'badge-danger' : 'badge-warning';
    }
    return 'badge-warning';
}

// Select Satellite
async function selectSatellite(name) {
    try {
        selectedSatellite = name;
        renderSatellites();

        await api.selectSatellite(name);
        await api.setMode('sgp4');
        await api.setTracking(true);

        showToast(`Tracking ${name}`, 'success');
        updateStatus();
    } catch (error) {
        showToast(`Failed to select satellite: ${error.message}`, 'danger');
    }
}

// Stop Tracking
async function stopTracking() {
    try {
        await api.setTracking(false);
        showToast('Tracking stopped', 'success');
        updateStatus();
    } catch (error) {
        showToast(`Failed to stop tracking: ${error.message}`, 'danger');
    }
}

// Refresh TLE
async function refreshTLE() {
    if (!selectedSatellite) return;

    try {
        setEnabled('refresh-tle-btn', false);
        updateText('refresh-tle-btn', 'Refreshing...');

        await api.refreshTLE(selectedSatellite);
        showToast('TLE refreshed successfully', 'success');
        await loadSatellites();
    } catch (error) {
        showToast(`Failed to refresh TLE: ${error.message}`, 'danger');
    } finally {
        setEnabled('refresh-tle-btn', true);
        updateText('refresh-tle-btn', 'Refresh TLE');
    }
}

// Manual TLE
async function submitManualTLE() {
    const name = document.getElementById('manual-name').value;
    const tleText = document.getElementById('manual-tle').value;

    // Parse lines from text area
    const lines = tleText.split('\n').map(l => l.trim()).filter(l => l.length > 0);

    if (lines.length < 2) {
        showToast('Please paste both TLE lines', 'warning');
        return;
    }

    const line1 = lines[0];
    const line2 = lines[1];

    if (!name || !line1 || !line2) {
        showToast('Please fill in all fields', 'warning');
        return;
    }

    try {
        setEnabled('manual-tle-btn', false);
        updateText('manual-tle-btn', 'Loading...');

        // Ensure we are in SGP4 mode first? API handles check.
        // But we might need to switch first.
        // Let's try to switch to SGP4 mode first just in case
        await api.setMode('sgp4');

        const result = await api.setManualTLE(name, line1, line2);
        showToast(result.message || 'Manual TLE loaded', 'success');
        updateStatus();
    } catch (error) {
        showToast(`Failed to load TLE: ${error.message}`, 'danger');
    } finally {
        setEnabled('manual-tle-btn', true);
        updateText('manual-tle-btn', 'Load TLE');
    }
}

// Update Status
async function updateStatus() {
    try {
        const status = await api.getStatus();

        if (status.mode === 'sgp4' && status.tracking) {
            // Show tracking info
            setVisible('tracking-info', false);
            setVisible('tracking-controls', true);

            const badge = document.getElementById('tracking-badge');
            badge.textContent = 'Tracking';
            badge.className = 'badge badge-success';

            // Update position
            if (status.position) {
                updateText('sat-lat', formatLatLon(status.position.lat, 0).split(',')[0]);
                updateText('sat-lon', formatLatLon(0, status.position.lon).split(',')[1]);
                updateText('sat-alt', formatAltitude(status.position.alt));
            }

            selectedSatellite = status.satellite;
            renderSatellites();
        } else {
            // Not tracking
            setVisible('tracking-info', true);
            setVisible('tracking-controls', false);

            const badge = document.getElementById('tracking-badge');
            badge.textContent = 'Not Tracking';
            badge.className = 'badge badge-warning';
        }
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}
