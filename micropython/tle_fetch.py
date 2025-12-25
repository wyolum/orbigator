"""
TLE Fetching Utility for Orbigator
Downloads Two-Line Element sets from CelesTrak
"""

import urequests
import json

CELESTRAK_BASE = "https://celestrak.org/NORAD/elements/gp.php"
CACHE_FILE = "tle_cache.json"

# Popular satellites
SATELLITES = {
    "ISS": "ISS (ZARYA)",
    "TIANGONG": "TIANGONG",
    "HST": "HST",
    "STARLINK-1": "STARLINK-1007",
}

def fetch_tle(satellite_name):
    """
    Fetch TLE from CelesTrak for a specific satellite.
    
    Args:
        satellite_name: Name of satellite (e.g., "ISS (ZARYA)")
    
    Returns:
        Tuple of (name, line1, line2) or None on error
    """
    try:
        url = f"{CELESTRAK_BASE}?NAME={satellite_name}&FORMAT=TLE"
        print(f"Fetching TLE for {satellite_name}...")
        
        response = urequests.get(url)
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return None
        
        lines = response.text.strip().split('\n')
        response.close()
        
        if len(lines) < 3:
            print("Error: Invalid TLE format")
            return None
        
        name = lines[0].strip()
        line1 = lines[1].strip()
        line2 = lines[2].strip()
        
        print(f"✓ Fetched TLE for {name}")
        return (name, line1, line2)
        
    except Exception as e:
        print(f"Error fetching TLE: {e}")
        return None

def fetch_station_tles():
    """Fetch TLEs for popular space stations."""
    tles = {}
    for key, name in SATELLITES.items():
        tle = fetch_tle(name)
        if tle:
            tles[key] = tle
    return tles

def cache_tle(name, tle_data):
    """Save TLE to cache file."""
    try:
        # Load existing cache
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
        
        # Add/update TLE
        cache[name] = {
            'name': tle_data[0],
            'line1': tle_data[1],
            'line2': tle_data[2]
        }
        
        # Save cache
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
        
        print(f"✓ Cached TLE for {name}")
        return True
        
    except Exception as e:
        print(f"Error caching TLE: {e}")
        return False

def load_cached_tle(name):
    """Load TLE from cache file."""
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        if name in cache:
            tle = cache[name]
            return (tle['name'], tle['line1'], tle['line2'])
        else:
            print(f"TLE for {name} not in cache")
            return None
            
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None

def test_tle_fetch():
    """Test TLE fetching."""
    print("="*60)
    print("Testing TLE Fetch")
    print("="*60)
    
    # Fetch ISS TLE
    tle = fetch_tle("ISS")
    if tle:
        print(f"\nName:  {tle[0]}")
        print(f"Line1: {tle[1]}")
        print(f"Line2: {tle[2]}")
        
        # Cache it
        cache_tle("ISS", tle)
        
        # Load from cache
        cached = load_cached_tle("ISS")
        if cached:
            print("\n✓ Cache test passed")
    else:
        print("✗ Failed to fetch TLE")

if __name__ == "__main__":
    test_tle_fetch()
