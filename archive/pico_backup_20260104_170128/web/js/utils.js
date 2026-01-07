// Utility Functions

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';

    const colors = {
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#2563eb'
    };

    toast.style.borderLeftColor = colors[type] || colors.info;
    toast.style.borderLeftWidth = '4px';
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format Numbers
function formatDegrees(deg) {
    return `${deg.toFixed(2)}°`;
}

function formatLatLon(lat, lon) {
    const latDir = lat >= 0 ? 'N' : 'S';
    const lonDir = lon >= 0 ? 'E' : 'W';
    return `${Math.abs(lat).toFixed(2)}°${latDir}, ${Math.abs(lon).toFixed(2)}°${lonDir}`;
}

function formatAltitude(alt) {
    return `${alt.toFixed(1)} km`;
}

// Loading Spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.style.margin = '2rem auto';
    element.innerHTML = '';
    element.appendChild(spinner);
}

// Update Element Text
function updateText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// Update Element HTML
function updateHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}

// Get Element Value
function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : null;
}

// Set Element Value
function setValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
}

// Enable/Disable Element
function setEnabled(id, enabled) {
    const el = document.getElementById(id);
    if (el) el.disabled = !enabled;
}

// Show/Hide Element
function setVisible(id, visible) {
    const el = document.getElementById(id);
    if (el) {
        if (visible) {
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    }
}

// Polling Helper
class Poller {
    constructor(callback, interval = 2000) {
        this.callback = callback;
        this.interval = interval;
        this.timer = null;
    }

    start() {
        if (this.timer) return;
        this.callback(); // Run immediately
        this.timer = setInterval(() => this.callback(), this.interval);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
}
