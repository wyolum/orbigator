"""
Test Plan13 with REAL ISS TLE from CelesTrak format
"""

from plan13 import satpredict, tle_fields
import time

# Real ISS TLE from CelesTrak (properly formatted)
# This is the exact format Plan13 expects
ISS_TLE = """ISS (ZARYA)
1 25544U 98067A   24360.50000000  .00016717  00000-0  29767-3 0  9992
2 25544  51.6416 208.3910 0005419  34.5884  60.2346 15.50103472479879
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
        
        # Parse TLE and predict
        for tledata in tle_fields(ISS_TLE).nextsatellite():
            satlat, satlon, sataz, satel, satx, saty = satp.sat_predict(tledata)
            
            print(f"\nSatellite: {satp.sat.name}")
            print(f"Observer: {MyLAT:.2f}°N, {MyLON:.2f}°E, {MyALT:.0f}m")
            print(f"Time: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
            
            print(f"\nCurrent Position:")
            print(f"  Lat/Lon:    {satlat:7.3f}°, {satlon:7.3f}°")
            print(f"  Azimuth:    {sataz:6.1f}°")
            print(f"  Elevation:  {satel:6.1f}°")
            print(f"  Range:      {satp.sat.rg:7.1f} km")
            print(f"  Altitude:   {satp.sat.alt:6.1f} km")
            
            # Distance variation over one orbit
            print("\n" + "="*60)
            print("Distance to ISS over one complete orbit:")
            print("="*60)
            
            period_min = 1440.0 / satp.sat.n0
            samples = 10
            ranges = []
            
            for i in range(samples + 1):
                offset_min = (i / samples) * period_min
                offset_sec = int(offset_min * 60)
                
                new_sec = (second + offset_sec) % 60
                new_min = (minute + (second + offset_sec) // 60) % 60
                new_hr = (hour + (minute + (second + offset_sec) // 60) // 60) % 24
                
                satp.settime(year, month, day, new_hr, new_min, new_sec)
                _, _, az, el, _, _ = satp.sat_predict(tledata)
                
                ranges.append(satp.sat.rg)
                
                visible = "VISIBLE" if el > 0 else ""
                print(f"  +{offset_min:5.1f} min: {satp.sat.rg:7.1f} km  "
                      f"Az={az:6.1f}° El={el:5.1f}°  {visible}")
            
            min_rg = min(ranges)
            max_rg = max(ranges)
            variation = max_rg - min_rg
            
            print(f"\n  Orbital Period:  {period_min:.2f} minutes")
            print(f"  Min Range:       {min_rg:.1f} km")
            print(f"  Max Range:       {max_rg:.1f} km")
            print(f"  Variation:       {variation:.1f} km ({variation/min_rg*100:.1f}%)")
            
            print("\n✓ Plan13 works! Distance varies by ~{:.0f} km over one orbit".format(variation))
            return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import sys
        sys.print_exception(e)
        return False

if __name__ == "__main__":
    test_plan13()
