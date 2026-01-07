# SGP4 Integration - Testing Guide

## Current Status (Dec 25, 2024)

### ✅ Completed
- SGP4 propagator integrated into Orbigator
- Satellite catalog created (ISS, Hubble, Tiangong, Starlink)
- TLE caching and WiFi fetching working
- Menu system updated with "Track Satellite" option
- GMST calculation for accurate geodetic conversion
- **Critical bug fixed**: Added missing epoch_year/epoch_day variables

### 🔧 Files Modified
- `micropython/modes.py` - Added SGP4Mode class
- `micropython/orb_utils.py` - Added GMST and TLE utilities
- `micropython/satellite_catalog.py` - NEW
- `micropython/tle_cache.json` - NEW

### 🐛 Bugs Fixed
1. **WiFi connection** - Changed from `wifi_setup.connect()` to `wifi_setup.connect_wifi(ssid, password)`
2. **Epoch calculation** - Implemented proper TLE epoch → Unix timestamp conversion
3. **Variable scope** - Added missing `epoch_year` and `epoch_day` variable definitions

## Testing Instructions for Tomorrow

### Step-by-Step Test

1. **Power on Orbigator**
   - Should boot normally to menu

2. **Navigate to SGP4 Mode**
   - Menu → "Track Satellite" (2nd item)

3. **Select Satellite**
   - Rotate encoder to choose: ISS / Hubble / Tiangong / Starlink
   - Display shows satellite name and TLE age

4. **Start Tracking** ⚠️ CRITICAL STEP
   - **Press the ENCODER BUTTON** (push the rotary encoder)
   - Should print: "Tracking ISS" (or selected satellite)
   - Motors should immediately move to satellite position

5. **Verify Real-Time Tracking**
   - Display should show:
     - Satellite name
     - Current lat/lon/alt
     - TLE age
   - Motors should continuously update position
   - For ISS: longitude should change ~4°/minute

### Button Functions in SGP4 Mode

| Button | Function |
|--------|----------|
| **Encoder Rotate** | Select satellite (ISS/Hubble/Tiangong/Starlink) |
| **Encoder Press** | ⭐ **Toggle tracking ON/OFF** |
| **Confirm** | Force TLE refresh via WiFi |
| **Back** | Return to main menu |

### Expected Behavior

**ISS Tracking:**
- Latitude: -51.6° to +51.6° (oscillating, ~90 min period)
- Longitude: Continuously increasing, ~4°/minute
- Altitude: ~400-420 km
- AoV motor: Follows latitude (0° to 180° range)
- EQX motor: Follows longitude (0° to 360° range)

### Troubleshooting

**If motors don't move:**
1. Check if "Tracking ISS" printed (confirms encoder press worked)
2. Check display shows lat/lon updating
3. Look for error messages in output
4. Verify motors respond in normal "Orbit!" mode

**If position doesn't update:**
1. Check for NameError or other Python errors
2. Verify epoch calculation is working
3. Check RTC time is correct

**If TLE fetch fails:**
1. Verify `wifi_config.json` exists
2. Check WiFi credentials
3. Cached TLEs will still work for tracking

## Code Locations

### SGP4Mode Class
File: `micropython/modes.py`
- Lines ~685-924
- Key methods:
  - `enter()` - Initialize mode, load TLEs
  - `_load_satellite(index)` - Parse TLE and init SGP4
  - `_fetch_tle()` - WiFi TLE refresh
  - `update(dt)` - **Real-time position calculation**
  - `on_encoder_press()` - Toggle tracking

### Epoch Calculation (Fixed)
File: `micropython/modes.py`, lines 850-868
```python
# Get epoch from SGP4 object
epoch_year = self.sgp4.epoch_year
epoch_day = self.sgp4.epoch_day

# Convert TLE epoch to Unix timestamp
epoch_jan1 = time.mktime((epoch_year, 1, 1, 0, 0, 0, 0, 0))
epoch_timestamp = epoch_jan1 + (epoch_day - 1.0) * 86400.0

# Calculate minutes since TLE epoch
elapsed_sec = now - epoch_timestamp
t_min = elapsed_sec / 60.0
```

## Next Steps

### If Tracking Works ✅
- Test with different satellites (Hubble, Tiangong)
- Verify TLE auto-refresh after 24 hours
- Test mode transitions (SGP4 → Menu → Orbit → SGP4)
- Confirm baseline "Orbit!" mode still works

### If Issues Remain 🐛
- Check for Python errors in output
- Verify `self.tracking` flag is set
- Add debug prints to `update()` method
- Test SGP4 propagator standalone with `test_sgp4_simple.py`

## Files Ready for Upload

All files are already on the Pico 2W:
- ✅ `modes.py` (with all fixes)
- ✅ `orb_utils.py` (with GMST)
- ✅ `satellite_catalog.py`
- ✅ `tle_cache.json`
- ✅ `sgp4.py`
- ✅ `tle_fetch.py`

Just power on and test!
