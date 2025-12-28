// Dashboard Logic

let statusPoller = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateStatus();
    statusPoller = new Poller(updateStatus, 60000);
    statusPoller.start();
});

// Update Status
async function updateStatus() {
    try {
        const status = await api.getStatus();

        // Update mode
        updateText('mode-badge', status.mode.toUpperCase());

        // Update motor positions
        if (status.motors) {
            updateText('aov-position', formatDegrees(status.motors.aov));
            updateText('eqx-position', formatDegrees(status.motors.eqx));
        }

        // Update WiFi status
        if (status.wifi) {
            const wifiEl = document.getElementById('wifi-status');
            if (status.wifi.connected) {
                wifiEl.textContent = `Connected (${status.wifi.ssid})`;
                wifiEl.className = 'badge badge-success';
            } else {
                wifiEl.textContent = 'Disconnected';
                wifiEl.className = 'badge badge-danger';
            }
        }

        // Update RTC status
        if (status.rtc) {
            const rtcEl = document.getElementById('rtc-status');
            if (status.rtc.synced) {
                rtcEl.textContent = 'Synced';
                rtcEl.className = 'badge badge-success';
            } else {
                rtcEl.textContent = 'Not Synced';
                rtcEl.className = 'badge badge-warning';
            }
        }

    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

// Switch Mode
async function switchMode(mode) {
    try {
        await api.setMode(mode);
        showToast(`Switched to ${mode.toUpperCase()} mode`, 'success');
        updateStatus();
    } catch (error) {
        showToast(`Failed to switch mode: ${error.message}`, 'danger');
    }
}

// Nudge Motor
async function nudgeMotor(motor, delta) {
    try {
        await api.nudgeMotor(motor, delta);
        showToast(`Nudged ${motor.toUpperCase()} by ${delta}°`, 'success');
        updateStatus();
    } catch (error) {
        showToast(`Failed to nudge motor: ${error.message}`, 'danger');
    }
}
