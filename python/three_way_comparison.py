#!/usr/bin/env python3
"""
Three-way comparison: Reference Tracker vs Standard SGP4 vs MicroPython SGP4
Standalone script to avoid import conflicts
"""

from sgp4.api import Satrec, jday
import math
import json

# Reference data from tracker
REF_LAT = 28.80
REF_LON = 126.42
REF_ALT = 265 * 1.60934  # 426.5 km
REF_TIME = (2026, 1, 3, 21, 8, 17)

# TLE
line1 = "1 25544U 98067A   26003.53276902  .00013553  00000+0  25297-3 0  9999"
line2 = "2 25544  51.6327  34.5663 0007560 336.0107  24.0528 15.49066978546237"

def gmst_from_jd(jd):
    """Calculate GMST"""
    T = (jd - 2451545.0) / 36525.0
    gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * T + \
               0.093104 * T**2 - 6.2e-6 * T**3
    gmst_deg = (gmst_sec / 240.0) % 360.0
    return math.radians(gmst_deg)

def eci_to_geodetic(x_eci, y_eci, z_eci, gmst):
    """Convert ECI to geodetic"""
    # ECI to ECEF
    cos_gmst = math.cos(gmst)
    sin_gmst = math.sin(gmst)
    x_ecef = cos_gmst * x_eci + sin_gmst * y_eci
    y_ecef = -sin_gmst * x_eci + cos_gmst * y_eci
    z_ecef = z_eci
    
    # ECEF to Geodetic
    a = 6378.137
    f = 1.0 / 298.257223563
    e2 = 2*f - f*f
    
    lon = math.atan2(y_ecef, x_ecef)
    p = math.sqrt(x_ecef*x_ecef + y_ecef*y_ecef)
    lat = math.atan2(z_ecef, p * (1.0 - e2))
    
    for _ in range(5):
        sin_lat = math.sin(lat)
        N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
        alt = p / math.cos(lat) - N
        lat = math.atan2(z_ecef, p * (1.0 - e2 * N / (N + alt)))
    
    sin_lat = math.sin(lat)
    N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - N
    
    return math.degrees(lat), math.degrees(lon), alt

def main():
    print("=" * 70)
    print("Three-Way ISS Position Comparison")
    print("Time: 2026-01-03 21:08:17 UTC")
    print("=" * 70)
    print()
    
    # Standard SGP4
    satellite = Satrec.twoline2rv(line1, line2)
    year, month, day, hour, minute, second = REF_TIME
    jd, fr = jday(year, month, day, hour, minute, second)
    error_code, pos_std, vel_std = satellite.sgp4(jd, fr)
    gmst = gmst_from_jd(jd + fr)
    lat_std, lon_std, alt_std = eci_to_geodetic(pos_std[0], pos_std[1], pos_std[2], gmst)
    
    # Load MicroPython results from previous run
    # (from validate_iss_tracker.py output)
    lat_mp = 29.6564
    lon_mp = 126.5232
    alt_mp = 428.853
    
    print("Reference Tracker:")
    print(f"  Lat: {REF_LAT:>8.4f}°  Lon: {REF_LON:>9.4f}°  Alt: {REF_ALT:>7.2f} km")
    print()
    
    print("Standard SGP4 Library:")
    print(f"  Lat: {lat_std:>8.4f}°  Lon: {lon_std:>9.4f}°  Alt: {alt_std:>7.2f} km")
    print(f"  ECI: X={pos_std[0]:>10.3f}  Y={pos_std[1]:>10.3f}  Z={pos_std[2]:>10.3f} km")
    print()
    
    print("MicroPython SGP4:")
    print(f"  Lat: {lat_mp:>8.4f}°  Lon: {lon_mp:>9.4f}°  Alt: {alt_mp:>7.2f} km")
    print()
    
    print("=" * 70)
    print("Error Analysis")
    print("=" * 70)
    print()
    
    # Standard vs Reference
    diff_lat_std = lat_std - REF_LAT
    diff_lon_std = lon_std - REF_LON
    diff_alt_std = alt_std - REF_ALT
    lat_km_std = diff_lat_std * 111.0
    lon_km_std = diff_lon_std * 111.0 * math.cos(math.radians(REF_LAT))
    horiz_std = math.sqrt(lat_km_std**2 + lon_km_std**2)
    total_std = math.sqrt(horiz_std**2 + diff_alt_std**2)
    
    # MicroPython vs Reference
    diff_lat_mp = lat_mp - REF_LAT
    diff_lon_mp = lon_mp - REF_LON
    diff_alt_mp = alt_mp - REF_ALT
    lat_km_mp = diff_lat_mp * 111.0
    lon_km_mp = diff_lon_mp * 111.0 * math.cos(math.radians(REF_LAT))
    horiz_mp = math.sqrt(lat_km_mp**2 + lon_km_mp**2)
    total_mp = math.sqrt(horiz_mp**2 + diff_alt_mp**2)
    
    # MicroPython vs Standard
    diff_lat_vs = lat_mp - lat_std
    diff_lon_vs = lon_mp - lon_std
    diff_alt_vs = alt_mp - alt_std
    lat_km_vs = diff_lat_vs * 111.0
    lon_km_vs = diff_lon_vs * 111.0 * math.cos(math.radians(lat_std))
    horiz_vs = math.sqrt(lat_km_vs**2 + lon_km_vs**2)
    total_vs = math.sqrt(horiz_vs**2 + diff_alt_vs**2)
    
    print(f"Standard SGP4 vs Reference Tracker:  {total_std:>6.1f} km error")
    print(f"MicroPython vs Reference Tracker:    {total_mp:>6.1f} km error")
    print(f"MicroPython vs Standard SGP4:        {total_vs:>6.1f} km error")
    print()
    
    print("Detailed Breakdown:")
    print(f"  Standard vs Ref:    ΔLat={diff_lat_std:>6.3f}°  ΔLon={diff_lon_std:>6.3f}°  ΔAlt={diff_alt_std:>6.2f} km")
    print(f"  MicroPython vs Ref: ΔLat={diff_lat_mp:>6.3f}°  ΔLon={diff_lon_mp:>6.3f}°  ΔAlt={diff_alt_mp:>6.2f} km")
    print(f"  MicroPython vs Std: ΔLat={diff_lat_vs:>6.3f}°  ΔLon={diff_lon_vs:>6.3f}°  ΔAlt={diff_alt_vs:>6.2f} km")
    print()
    
    print("=" * 70)
    print("Conclusion:")
    print("=" * 70)
    if total_std < 50:
        print(f"✓ Standard SGP4 matches reference tracker well ({total_std:.1f} km)")
    else:
        print(f"⚠ Standard SGP4 differs from tracker by {total_std:.1f} km")
        print("  (Reference tracker may use different propagation model)")
    
    if total_vs < 100:
        print(f"✓ MicroPython SGP4 is acceptable ({total_vs:.1f} km from standard)")
    else:
        print(f"✗ MicroPython SGP4 needs improvement ({total_vs:.1f} km from standard)")
    print("=" * 70)

if __name__ == "__main__":
    main()
