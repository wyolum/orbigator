"""
Satellite Catalog for Orbigator
Defines available satellites for tracking
"""

# Format: (Display Name, NORAD ID)
SATELLITES = [
    ("ISS", "25544"),           # International Space Station
    ("HUBBLE", "20580"),        # Hubble Space Telescope
    ("TIANGONG", "48274"),      # Chinese Space Station
    ("STARLINK-1007", "44713"), # Example Starlink satellite
]

def get_satellite_list():
    """Return list of (name, norad_id) tuples."""
    return SATELLITES

def get_satellite_name(index):
    """Get satellite display name by index."""
    if 0 <= index < len(SATELLITES):
        return SATELLITES[index][0]
    return None

def get_satellite_norad(index):
    """Get satellite NORAD ID by index."""
    if 0 <= index < len(SATELLITES):
        return SATELLITES[index][1]
    return None

def get_satellite_count():
    """Return total number of satellites in catalog."""
    return len(SATELLITES)
