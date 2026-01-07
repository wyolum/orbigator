"""
TLE (Two-Line Element) Parser for Orbigator
Parses satellite orbital elements from TLE format
"""

import math

def parse_tle(line1, line2):
    """
    Parse a Two-Line Element set into orbital elements.
    
    TLE Format:
    Line 1: 1 NNNNNC NNNNNAAA NNNNN.NNNNNNNN +.NNNNNNNN +NNNNN-N +NNNNN-N N NNNNN
    Line 2: 2 NNNNN NNN.NNNN NNN.NNNN NNNNNNN NNN.NNNN NNN.NNNN NN.NNNNNNNNNNNNNN
    
    Args:
        line1: First line of TLE (69 characters)
        line2: Second line of TLE (69 characters)
    
    Returns:
        Dictionary with orbital elements
    """
    
    # Validate line numbers
    if line1[0] != '1' or line2[0] != '2':
        raise ValueError("Invalid TLE: Line numbers must be 1 and 2")
    
    # Validate checksums
    if not _verify_checksum(line1) or not _verify_checksum(line2):
        raise ValueError("Invalid TLE: Checksum mismatch")
    
    # Parse Line 1
    sat_number = int(line1[2:7])
    classification = line1[7]
    int_designator = line1[9:17].strip()
    
    # Epoch: YY DDD.DDDDDDDD
    epoch_year = int(line1[18:20])
    epoch_day = float(line1[20:32])
    
    # Convert 2-digit year to 4-digit (assume 1957-2056 range)
    if epoch_year < 57:
        epoch_year += 2000
    else:
        epoch_year += 1900
    
    # First derivative of mean motion (rev/day^2)
    ndot = float(line1[33:43])
    
    # Second derivative of mean motion (rev/day^3)
    # Format: +NNNNN-N means NNNNN x 10^-N
    nddot_str = line1[44:52].strip()
    nddot = _parse_decimal(nddot_str)
    
    # BSTAR drag term
    bstar_str = line1[53:61].strip()
    bstar = _parse_decimal(bstar_str)
    
    ephemeris_type = int(line1[62])
    element_number = int(line1[64:68])
    
    # Parse Line 2
    sat_number2 = int(line2[2:7])
    if sat_number != sat_number2:
        raise ValueError("Invalid TLE: Satellite numbers don't match")
    
    # Orbital elements
    inclination = float(line2[8:16])  # degrees
    raan = float(line2[17:25])  # Right Ascension of Ascending Node (degrees)
    eccentricity = float('0.' + line2[26:33])  # Implied decimal point
    arg_perigee = float(line2[34:42])  # Argument of perigee (degrees)
    mean_anomaly = float(line2[43:51])  # Mean anomaly (degrees)
    mean_motion = float(line2[52:63])  # Revolutions per day
    rev_number = int(line2[63:68])  # Revolution number at epoch
    
    # Compute derived values
    # Semi-major axis from mean motion (Kepler's 3rd law)
    # n = sqrt(mu/a^3) => a = (mu/n^2)^(1/3)
    # where n is in rad/min and mu = 398600.4418 km^3/s^2
    
    MU = 398600.4418  # Earth gravitational parameter (km^3/s^2)
    n_rad_min = mean_motion * 2.0 * math.pi / 1440.0  # Convert rev/day to rad/min
    n_rad_sec = n_rad_min / 60.0  # rad/s
    
    semi_major_axis = (MU / (n_rad_sec**2)) ** (1.0/3.0)  # km
    
    # Orbital period
    period_min = 1440.0 / mean_motion  # minutes
    
    # Altitude (approximate, assumes circular orbit)
    EARTH_RADIUS = 6378.137  # km
    altitude_km = semi_major_axis - EARTH_RADIUS
    
    return {
        # Satellite identification
        'sat_number': sat_number,
        'classification': classification,
        'int_designator': int_designator,
        
        # Epoch
        'epoch_year': epoch_year,
        'epoch_day': epoch_day,
        
        # Orbital elements (Keplerian)
        'inclination': inclination,  # degrees
        'raan': raan,  # degrees
        'eccentricity': eccentricity,
        'arg_perigee': arg_perigee,  # degrees
        'mean_anomaly': mean_anomaly,  # degrees
        'mean_motion': mean_motion,  # rev/day
        
        # Derived values
        'semi_major_axis': semi_major_axis,  # km
        'period_min': period_min,
        'altitude_km': altitude_km,
        
        # Perturbation parameters
        'ndot': ndot,  # rev/day^2
        'nddot': nddot,  # rev/day^3
        'bstar': bstar,  # drag term
        
        # Metadata
        'ephemeris_type': ephemeris_type,
        'element_number': element_number,
        'rev_number': rev_number
    }

def _verify_checksum(line):
    """Verify TLE line checksum."""
    if len(line) < 69:
        return False
    
    checksum = 0
    for char in line[0:68]:
        if char.isdigit():
            checksum += int(char)
        elif char == '-':
            checksum += 1
    
    checksum = checksum % 10
    expected = int(line[68])
    
    return checksum == expected

def _parse_decimal(s):
    """
    Parse decimal in TLE format: +NNNNN-N means NNNNN x 10^-N
    Example: " 12345-3" = 0.12345
    """
    s = s.strip()
    if not s or s == '0' or s == '+0' or s == '-0':
        return 0.0
    
    # Split mantissa and exponent
    if '-' in s[1:]:  # Negative exponent
        parts = s.split('-')
        mantissa = float(parts[0])
        exponent = -int(parts[1])
    elif '+' in s[1:]:  # Positive exponent
        parts = s.split('+')
        mantissa = float(parts[0])
        exponent = int(parts[1])
    else:
        return float(s)
    
    return mantissa * (10.0 ** exponent)

def format_tle_summary(tle_dict):
    """Format TLE data as human-readable summary."""
    lines = [
        f"Satellite: {tle_dict['sat_number']} ({tle_dict['int_designator']})",
        f"Epoch: Year {tle_dict['epoch_year']}, Day {tle_dict['epoch_day']:.2f}",
        f"",
        f"Orbital Elements:",
        f"  Inclination:    {tle_dict['inclination']:.4f}°",
        f"  RAAN:           {tle_dict['raan']:.4f}°",
        f"  Eccentricity:   {tle_dict['eccentricity']:.7f}",
        f"  Arg Perigee:    {tle_dict['arg_perigee']:.4f}°",
        f"  Mean Anomaly:   {tle_dict['mean_anomaly']:.4f}°",
        f"  Mean Motion:    {tle_dict['mean_motion']:.8f} rev/day",
        f"",
        f"Derived:",
        f"  Altitude:       {tle_dict['altitude_km']:.1f} km",
        f"  Period:         {tle_dict['period_min']:.2f} min",
        f"  Semi-major:     {tle_dict['semi_major_axis']:.1f} km"
    ]
    return '\n'.join(lines)

# Test with ISS TLE
if __name__ == "__main__":
    # ISS TLE (example)
    line1 = "1 25544U 98067A   24360.50000000  .00016717  00000-0  10270-3 0  9005"
    line2 = "2 25544  51.6400 123.4567 0001234  12.3456 123.4567 15.50103472123456"
    
    try:
        tle = parse_tle(line1, line2)
        print(format_tle_summary(tle))
    except Exception as e:
        print(f"Error: {e}")
