"""
Compare geodetic conversion results between standard library and MicroPython
"""

import subprocess
import re

def run_standard_conversion():
    """Run the standard Python implementation"""
    result = subprocess.run(
        ['bash', '-c', 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate the_basics && python python/eci_to_geodetic.py'],
        cwd='/home/justin/code/orbigator',
        capture_output=True,
        text=True
    )
    return result.stdout

def run_micropython_conversion():
    """Run the MicroPython implementation"""
    result = subprocess.run(
        ['bash', '-c', 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate the_basics && python micropython/eci_to_geodetic_test.py'],
        cwd='/home/justin/code/orbigator',
        capture_output=True,
        text=True
    )
    return result.stdout

def extract_geodetic(output, satellite="ISS"):
    """Extract geodetic coordinates from output"""
    lines = output.split('\n')
    in_satellite = False
    geo = {}
    
    for i, line in enumerate(lines):
        if f"Satellite: {satellite}" in line:
            in_satellite = True
        elif in_satellite:
            if "Latitude:" in line and "Geodetic" in lines[i-1]:
                geo['latitude'] = float(line.split(':')[1].strip().replace('°', ''))
            elif "Longitude:" in line and 'latitude' in geo:
                geo['longitude'] = float(line.split(':')[1].strip().replace('°', ''))
            elif "Altitude:" in line and 'longitude' in geo:
                geo['altitude'] = float(line.split(':')[1].strip().replace('km', ''))
                break
    
    return geo

def main():
    print("=" * 70)
    print("Geodetic Conversion Comparison")
    print("=" * 70)
    print()
    
    print("Running standard Python implementation...")
    standard_output = run_standard_conversion()
    
    print("Running MicroPython implementation...")
    micropython_output = run_micropython_conversion()
    
    print()
    print("=" * 70)
    print("RESULTS COMPARISON - ISS")
    print("=" * 70)
    print()
    
    # Extract geodetic coordinates
    std_geo = extract_geodetic(standard_output, "ISS")
    mp_geo = extract_geodetic(micropython_output, "ISS")
    
    if not std_geo or not mp_geo:
        print("ERROR: Could not extract geodetic data")
        print("\nStandard output:")
        print(standard_output)
        print("\nMicroPython output:")
        print(micropython_output)
        return
    
    print("Standard Python Library:")
    print(f"  Latitude:  {std_geo['latitude']:>9.4f}°")
    print(f"  Longitude: {std_geo['longitude']:>9.4f}°")
    print(f"  Altitude:  {std_geo['altitude']:>9.3f} km")
    print()
    
    print("MicroPython Implementation:")
    print(f"  Latitude:  {mp_geo['latitude']:>9.4f}°")
    print(f"  Longitude: {mp_geo['longitude']:>9.4f}°")
    print(f"  Altitude:  {mp_geo['altitude']:>9.3f} km")
    print()
    
    # Calculate differences
    diff_lat = mp_geo['latitude'] - std_geo['latitude']
    diff_lon = mp_geo['longitude'] - std_geo['longitude']
    diff_alt = mp_geo['altitude'] - std_geo['altitude']
    
    print("Differences (MicroPython - Standard):")
    print(f"  ΔLatitude:  {diff_lat:>9.4f}°")
    print(f"  ΔLongitude: {diff_lon:>9.4f}°")
    print(f"  ΔAltitude:  {diff_alt:>9.3f} km")
    print()
    
    # Calculate distance error (approximate)
    import math
    # Convert lat/lon difference to km (rough approximation)
    lat_km = diff_lat * 111.0  # 1 degree latitude ≈ 111 km
    lon_km = diff_lon * 111.0 * math.cos(math.radians(std_geo['latitude']))  # longitude varies with latitude
    
    horizontal_error = math.sqrt(lat_km**2 + lon_km**2)
    total_error = math.sqrt(horizontal_error**2 + diff_alt**2)
    
    print("Error Estimates:")
    print(f"  Horizontal: {horizontal_error:>9.3f} km")
    print(f"  Vertical:   {abs(diff_alt):>9.3f} km")
    print(f"  Total 3D:   {total_error:>9.3f} km")
    print()
    
    print("=" * 70)
    
    # Determine if acceptable
    if total_error < 10:
        print("✓ EXCELLENT: Total error < 10 km")
    elif total_error < 50:
        print("✓ GOOD: Total error < 50 km")
    elif total_error < 100:
        print("⚠ ACCEPTABLE: Total error < 100 km")
    else:
        print("✗ POOR: Total error > 100 km - needs investigation")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
