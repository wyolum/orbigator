"""
Compare SGP4 results between standard library and MicroPython implementation
"""

import subprocess
import json
import sys

def run_standard_sgp4():
    """Run the standard SGP4 implementation"""
    result = subprocess.run(
        ['bash', '-c', 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate the_basics && python python/sgp4_desktop_test.py'],
        cwd='/home/justin/code/orbigator',
        capture_output=True,
        text=True
    )
    return result.stdout

def run_micropython_sgp4():
    """Run the MicroPython SGP4 implementation"""
    result = subprocess.run(
        ['bash', '-c', 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate the_basics && python micropython/sgp4_test.py'],
        cwd='/home/justin/code/orbigator',
        capture_output=True,
        text=True
    )
    return result.stdout

def extract_eci_position(output, satellite="ISS"):
    """Extract ECI position from output"""
    lines = output.split('\n')
    in_satellite = False
    position = {}
    
    for i, line in enumerate(lines):
        if f"Satellite: {satellite}" in line:
            in_satellite = True
        elif in_satellite:
            if "X:" in line and "ECI Position" in lines[i-1]:
                position['x'] = float(line.split(':')[1].strip())
            elif "Y:" in line and 'x' in position:
                position['y'] = float(line.split(':')[1].strip())
            elif "Z:" in line and 'y' in position:
                position['z'] = float(line.split(':')[1].strip())
            elif "Magnitude:" in line and 'z' in position:
                position['magnitude'] = float(line.split(':')[1].strip())
                break
    
    return position

def main():
    print("=" * 70)
    print("SGP4 Implementation Comparison")
    print("=" * 70)
    print()
    
    print("Running standard SGP4 library...")
    standard_output = run_standard_sgp4()
    
    print("Running MicroPython SGP4 implementation...")
    micropython_output = run_micropython_sgp4()
    
    print()
    print("=" * 70)
    print("RESULTS COMPARISON - ISS")
    print("=" * 70)
    print()
    
    # Extract positions
    std_pos = extract_eci_position(standard_output, "ISS")
    mp_pos = extract_eci_position(micropython_output, "ISS")
    
    if not std_pos or not mp_pos:
        print("ERROR: Could not extract position data")
        print("\nStandard output:")
        print(standard_output)
        print("\nMicroPython output:")
        print(micropython_output)
        return
    
    print("Standard SGP4 Library:")
    print(f"  X: {std_pos['x']:>12.3f} km")
    print(f"  Y: {std_pos['y']:>12.3f} km")
    print(f"  Z: {std_pos['z']:>12.3f} km")
    print(f"  Magnitude: {std_pos['magnitude']:>12.3f} km")
    print()
    
    print("MicroPython SGP4:")
    print(f"  X: {mp_pos['x']:>12.3f} km")
    print(f"  Y: {mp_pos['y']:>12.3f} km")
    print(f"  Z: {mp_pos['z']:>12.3f} km")
    print(f"  Magnitude: {mp_pos['magnitude']:>12.3f} km")
    print()
    
    # Calculate differences
    diff_x = mp_pos['x'] - std_pos['x']
    diff_y = mp_pos['y'] - std_pos['y']
    diff_z = mp_pos['z'] - std_pos['z']
    diff_mag = mp_pos['magnitude'] - std_pos['magnitude']
    
    import math
    position_error = math.sqrt(diff_x**2 + diff_y**2 + diff_z**2)
    
    print("Differences (MicroPython - Standard):")
    print(f"  ΔX: {diff_x:>12.3f} km")
    print(f"  ΔY: {diff_y:>12.3f} km")
    print(f"  ΔZ: {diff_z:>12.3f} km")
    print(f"  ΔMagnitude: {diff_mag:>12.3f} km")
    print(f"  Position Error: {position_error:>12.3f} km")
    print()
    
    # Percentage errors
    print("Percentage Errors:")
    print(f"  X: {abs(diff_x/std_pos['x'])*100:>8.4f}%")
    print(f"  Y: {abs(diff_y/std_pos['y'])*100:>8.4f}%")
    print(f"  Z: {abs(diff_z/std_pos['z'])*100:>8.4f}%")
    print(f"  Magnitude: {abs(diff_mag/std_pos['magnitude'])*100:>8.4f}%")
    print()
    
    print("=" * 70)
    
    # Determine if acceptable
    if position_error < 10:  # Less than 10 km error
        print("✓ EXCELLENT: Position error < 10 km")
    elif position_error < 50:
        print("✓ GOOD: Position error < 50 km")
    elif position_error < 100:
        print("⚠ ACCEPTABLE: Position error < 100 km")
    else:
        print("✗ POOR: Position error > 100 km - needs investigation")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
