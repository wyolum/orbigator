"""
Test Plan13 with REAL ISS TLE from CelesTrak format
"""

from plan13 import satpredict, tle_fields
import time

# Real ISS TLE from n2yo.com (Dec 25, 2024)
# This is the exact format Plan13 expects
ISS_TLE = """ISS (ZARYA)
1 25544U 98067A   25359.56752749  .00014081  00000-0  25591-3 0  9998
2 25544  51.6318  78.9495 0003224 299.9641  60.1027 15.49813539544848
"""

def test_plan13():
    """Test Plan13 satellite tracking with distance comparison."""
    print("="*60)
    print("Testing Plan13 with ISS TLE")
    print("="*60)
    
    try:
        # Observer location (WyoLum - Boulder area)
        MyLAT = 40.0
        MyLON = -105.0
        MyALT = 1600.0
        
        # Create satellite predictor
        satp = satpredict(MyLAT, MyLON, MyALT, 1150, 609)
        
        # Get current time
        now = time.localtime()
        year, month, day = now[0], now[1], now[2]
        hour, minute, second = now[3], now[4], now[5]
        
        # Set time
        satp.settime(year, month, day, hour, minute, second)
        
        # Parse TLE - tle_fields expects a LIST of lines, not a string
        tle_lines = ISS_TLE.strip().split('\n')
        
        # Parse and predict - pass the list directly
        for tledata in tle_fields(tle_lines).nextsatellite():
            satlat, satlon, sataz, satel, satx, saty = satp.sat_predict(tledata)
            
            print(f"\nSatellite: {satp.sat.name}")
            print(f"Observer: {MyLAT:.2f}°N, {MyLON:.2f}°E, {MyALT:.0f}m")
            print(f"Time: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
            
            print(f"\nCurrent Position:")
            print(f"  Lat/Lon:    {satlat:7.3f}°, {satlon:7.3f}°")
            print(f"  Azimuth:    {sataz:6.1f}°")
            print(f"  Elevation:  {satel:6.1f}°")
            
            # Compute range from satellite position vector
            # sat.S is [x, y, z] in km from Earth center
            # Observer position is in curpos
            import math
            dx = satp.sat.S[0] - satp.curpos.O[0]
            dy = satp.sat.S[1] - satp.curpos.O[1]
            dz = satp.sat.S[2] - satp.curpos.O[2]
            range_km = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Altitude from Earth center
            sat_r = math.sqrt(satp.sat.S[0]**2 + satp.sat.S[1]**2 + satp.sat.S[2]**2)
            altitude_km = sat_r - 6378.137  # Earth radius
            
            print(f"  Altitude:   {altitude_km:.1f} km")
            print(f"  Range:      {range_km:.1f} km")
            
            # Distance variation over one orbit
            print("\n" + "="*60)
            print("Distance to ISS over one complete orbit:")
            print("="*60)
            
            # Compute orbital period from TLE mean motion (rev/day)
            # tledata is (name, line1, line2)
            line2 = tledata[2]
            mean_motion = float(line2[52:63])  # rev/day
            period_min = 1440.0 / mean_motion
            samples = 10
            ranges = []
            
            for i in range(samples + 1):
                offset_min = (i / samples) * period_min
                offset_sec = int(offset_min * 60)
                
                # Compute new time
                new_sec = (second + offset_sec) % 60
                new_min = (minute + (second + offset_sec) // 60) % 60
                new_hr = (hour + (minute + (second + offset_sec) // 60) // 60) % 24
                
                satp.settime(year, month, day, new_hr, new_min, new_sec)
                _, _, az, el, _, _ = satp.sat_predict(tledata)
                
                # Compute range at this time
                dx = satp.sat.S[0] - satp.curpos.O[0]
                dy = satp.sat.S[1] - satp.curpos.O[1]
                dz = satp.sat.S[2] - satp.curpos.O[2]
                r = math.sqrt(dx*dx + dy*dy + dz*dz)
                ranges.append(r)
                
                visible = "VIS" if el > 0 else ""
                print(f"  +{offset_min:5.1f} min: {r:7.1f} km  "
                      f"Az={az:5.0f}° El={el:5.0f}°  {visible}")
            
            min_rg = min(ranges)
            max_rg = max(ranges)
            variation = max_rg - min_rg
            
            print(f"\n  Orbital Period:  {period_min:.2f} minutes")
            print(f"  Min Range:       {min_rg:.1f} km")
            print(f"  Max Range:       {max_rg:.1f} km")
            print(f"  Variation:       {variation:.1f} km ({variation/min_rg*100:.1f}%)")
            
            print("\n✓ Plan13 works! ISS position calculated successfully!")
            print(f"\nThe ISS is currently over ({satlat:.1f}°, {satlon:.1f}°)")
            print(f"From your location, it's at Az={sataz:.0f}° El={satel:.0f}°")
            
            if satel > 0:
                print("*** ISS IS VISIBLE from your location! ***")
            else:
                print("(ISS is below the horizon)")
            
            return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import sys
        sys.print_exception(e)
        return False

if __name__ == "__main__":
    test_plan13()
