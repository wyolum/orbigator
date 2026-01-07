// Orbit Mode Logic

// Presets
const PRESETS = {
    iss: { altitude_km: 400, period_min: 92.5, eccentricity: 0.001, inclination_deg: 51.6 },
    geo: { altitude_km: 35786, period_min: 1436, eccentricity: 0.0, inclination_deg: 0.0 },
    leo: { altitude_km: 600, period_min: 96.5, eccentricity: 0.0, inclination_deg: 98.0 }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentParams();
});

// Load Current Parameters
async function loadCurrentParams() {
    try {
        const status = await api.getStatus();
        if (status.orbital_params) {
            setValue('altitude-slider', status.orbital_params.altitude_km);
            setValue('period-input', status.orbital_params.period_min);
            setValue('eccentricity-input', status.orbital_params.eccentricity);
            setValue('inclination-input', status.orbital_params.inclination_deg);
            updateAltitudeDisplay();
        }
    } catch (error) {
        console.error('Failed to load parameters:', error);
    }
}

// Update Altitude Display
function updateAltitudeDisplay() {
    const value = getValue('altitude-slider');
    updateText('altitude-value', value);
}

// Apply Parameters
async function applyParams() {
    try {
        const params = {
            altitude_km: parseFloat(getValue('altitude-slider')),
            period_min: parseFloat(getValue('period-input')),
            eccentricity: parseFloat(getValue('eccentricity-input')),
            inclination_deg: parseFloat(getValue('inclination-input'))
        };

        const result = await api.setOrbitParams(params);

        if (result.params) {
            updateText('aov-rate', result.params.aov_rate.toFixed(6));
            updateText('eqx-rate', result.params.eqx_rate.toFixed(6));
        }

        await api.setMode('orbit');
        showToast('Orbital parameters applied', 'success');
    } catch (error) {
        showToast(`Failed to apply parameters: ${error.message}`, 'danger');
    }
}

// Load Preset
function loadPreset(name) {
    const preset = PRESETS[name];
    if (!preset) return;

    setValue('altitude-slider', preset.altitude_km);
    setValue('period-input', preset.period_min);
    setValue('eccentricity-input', preset.eccentricity);
    setValue('inclination-input', preset.inclination_deg);
    updateAltitudeDisplay();

    showToast(`Loaded ${name.toUpperCase()} preset`, 'success');
}
