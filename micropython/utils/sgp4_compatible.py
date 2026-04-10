"""
Kepler J2 Propagator with SGP4-Compatible Interface
====================================================

Drop-in replacement class that implements the same interface as SGP4
but uses Keplerian propagation with J2 perturbations.

Usage (exactly like SGP4):
    sat = SGP4()
    sat.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)
    x, y, z = sat.propagate(t_minutes)
    lat, lon, alt = sat.eci_to_geodetic(x, y, z, gmst)
"""

import math

# Constants
PI = math.pi
TWOPI = 2.0 * PI
DE2RA = 0.0174532925199433  # Degrees to radians
XKMPER = 6378.137  # Earth radius (km)
MU_EARTH = 398600.4418  # Earth gravitational parameter (km^3/s^2)
J2 = 0.00108263  # Earth's J2 (oblateness coefficient)


class SGP4:
    """
    Keplerian propagator with J2 perturbations.
    
    Compatible interface with SGP4 for easy drop-in replacement.
    """
    
    def __init__(self):
        """Initialize empty propagator."""
        pass
    
    def init(self, epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n):
        """
        Initialize orbital elements.
        
        Args:
            epoch_year: Epoch year (e.g., 2008)
            epoch_day: Day of year with fractional part (e.g., 264.51782528)
            bstar: Drag term (not used in this implementation)
            inc: Inclination (degrees)
            raan: Right Ascension of Ascending Node (degrees)
            ecc: Eccentricity
            argp: Argument of perigee (degrees)
            m: Mean anomaly (degrees)
            n: Mean motion (revolutions per day)
        """
        # Store epoch
        self.epoch_year = epoch_year
        self.epoch_day = epoch_day
        self.bstar = bstar  # Not used, but stored for compatibility
        
        # Convert orbital elements to radians
        self.inc = inc * DE2RA
        self.raan = raan * DE2RA
        self.ecc = ecc
        self.argp = argp * DE2RA
        self.m = m * DE2RA
        
        # Convert mean motion to rad/min
        self.n = n * TWOPI / 1440.0  # rev/day to rad/min
        
        # Convert to rad/sec for calculations
        n_rad_sec = n * TWOPI / 86400.0
        
        # Calculate semi-major axis from mean motion
        # n = sqrt(mu / a^3)  =>  a = (mu / n^2)^(1/3)
        self.aodp = (MU_EARTH / (n_rad_sec ** 2)) ** (1.0/3.0)  # km
        
        # Pre-calculate trig functions
        self.cosio = math.cos(self.inc)
        self.sinio = math.sin(self.inc)
        
        # Calculate J2 perturbation rates
        self._calculate_j2_rates()
    
    def _calculate_j2_rates(self):
        """Calculate secular rates due to J2 perturbations."""
        a = self.aodp
        e = self.ecc
        i = self.inc
        n = self.n  # rad/min
        
        # Common factor
        p = a * (1.0 - e * e)  # Semi-latus rectum
        factor = 1.5 * J2 * (XKMPER ** 2) * n / (p ** 2)
        
        cos_i_sq = self.cosio * self.cosio
        
        # Secular rates (radians per minute)
        # RAAN regression (nodal precession)
        self.xnodot = -factor * self.cosio
        
        # Argument of perigee rotation (apsidal precession)
        self.omgdot = factor * (2.5 * cos_i_sq - 0.5)
        
        # Mean motion correction
        sqrt_term = math.sqrt(1.0 - e * e)
        self.xmdot = n * (1.0 + factor * sqrt_term * (1.5 * cos_i_sq - 0.5) / n)
    
    def propagate(self, t_min):
        """
        Propagate orbit to get position.
        
        Args:
            t_min: Time since epoch in minutes
            
        Returns:
            (x, y, z) position in km (ECI frame)
        """
        # Update orbital elements with J2 secular effects
        m_curr = (self.m + self.xmdot * t_min) % TWOPI
        raan_curr = (self.raan + self.xnodot * t_min) % TWOPI
        argp_curr = (self.argp + self.omgdot * t_min) % TWOPI
        
        # Solve Kepler's equation for eccentric anomaly
        e_anom = m_curr
        for i in range(10):
            sin_e = math.sin(e_anom)
            cos_e = math.cos(e_anom)
            d_e = (m_curr - e_anom + self.ecc * sin_e) / (1.0 - self.ecc * cos_e)
            e_anom += d_e
            if abs(d_e) < 1e-8:
                break
        
        # Calculate true anomaly
        sin_e = math.sin(e_anom)
        cos_e = math.cos(e_anom)
        
        # Using atan2 for numerical stability
        sqrt_term = math.sqrt(1.0 - self.ecc * self.ecc)
        nu = math.atan2(sqrt_term * sin_e, cos_e - self.ecc)
        
        # Calculate radius
        r = self.aodp * (1.0 - self.ecc * cos_e)
        
        # Argument of latitude
        u = argp_curr + nu
        
        # Position in orbital plane (perifocal frame)
        x_prime = r * math.cos(u)
        y_prime = r * math.sin(u)
        
        # Rotate to ECI frame
        cos_raan = math.cos(raan_curr)
        sin_raan = math.sin(raan_curr)
        cos_inc = self.cosio
        sin_inc = self.sinio
        
        # Rotation matrix multiplication
        x = (x_prime * cos_raan - y_prime * cos_inc * sin_raan)
        y = (x_prime * sin_raan + y_prime * cos_inc * cos_raan)
        z = (y_prime * sin_inc)
        
        return (x, y, z)
    
    def eci_to_geodetic(self, x, y, z, gmst):
        """
        Convert ECI coordinates to geodetic latitude, longitude, altitude.
        
        Args:
            x, y, z: ECI position in km
            gmst: Greenwich Mean Sidereal Time in radians
            
        Returns:
            (lat, lon, alt) in radians, radians, km
        """
        # Calculate longitude (accounting for Earth rotation)
        r = math.sqrt(x*x + y*y)
        lon = math.atan2(y, x) - gmst
        
        # Normalize longitude to [-π, π]
        while lon > PI:
            lon -= TWOPI
        while lon < -PI:
            lon += TWOPI
        
        # Initial latitude estimate
        lat = math.atan2(z, r)
        
        # WGS84 ellipsoid parameters
        a = 6378.137  # Equatorial radius (km)
        f = 1.0 / 298.257223563  # Flattening
        e2 = 2*f - f*f  # Eccentricity squared
        
        # Iterative calculation for geodetic latitude
        phi = lat
        for i in range(5):
            sin_phi = math.sin(phi)
            c = a / math.sqrt(1.0 - e2 * sin_phi * sin_phi)
            phi = math.atan2(z + c * e2 * sin_phi, r)
        
        # Calculate altitude
        alt = r / math.cos(phi) - c
        
        return (phi, lon, alt)


# Helper function to calculate GMST
def calculate_gmst(year, day_of_year):
    """
    Calculate Greenwich Mean Sidereal Time.
    
    Args:
        year: Year (e.g., 2008)
        day_of_year: Day of year with fractional part (e.g., 264.51782528)
        
    Returns:
        GMST in radians
    """
    # Julian date at 0h UT
    # Simplified calculation for demonstration
    jd = 367 * year - int(7 * (year + int((0 + 9) / 12)) / 4) + \
         int(275 * 1 / 9) + day_of_year + 1721013.5
    
    # Julian centuries from J2000.0
    t = (jd - 2451545.0) / 36525.0
    
    # GMST at 0h UT (seconds)
    gmst_sec = 24110.54841 + 8640184.812866 * t + 0.093104 * t * t - 6.2e-6 * t * t * t
    
    # Convert to radians and normalize
    gmst = (gmst_sec / 240.0) * DE2RA  # 240 seconds = 1 degree
    gmst = gmst % TWOPI
    
    # Add rotation for time of day
    day_fraction = day_of_year - int(day_of_year)
    gmst += TWOPI * 1.00273790935 * day_fraction
    gmst = gmst % TWOPI
    
    return gmst


# Example usage demonstrating compatibility with SGP4 interface
if __name__ == "__main__":
    print("=" * 70)
    print("Kepler J2 Propagator - SGP4 Compatible Interface")
    print("=" * 70)
    
    # ISS orbital elements (from TLE)
    sat = SGP4()
    sat.init(
        epoch_year=2008,
        epoch_day=264.51782528,
        bstar=-0.000011606,
        inc=51.6416,
        raan=247.4627,
        ecc=0.0006703,
        argp=130.5360,
        m=325.0288,
        n=15.72125391
    )
    
    print(f"\nOrbital Elements:")
    print(f"  Semi-major axis: {sat.aodp:.3f} km")
    print(f"  Eccentricity: {sat.ecc:.7f}")
    print(f"  Inclination: {sat.inc * 180/PI:.4f}°")
    
    # Propagate at epoch
    print(f"\nPosition at Epoch (t=0):")
    x, y, z = sat.propagate(0.0)
    print(f"  X: {x:12.3f} km")
    print(f"  Y: {y:12.3f} km")
    print(f"  Z: {z:12.3f} km")
    
    r = math.sqrt(x*x + y*y + z*z)
    alt = r - XKMPER
    print(f"  Altitude: {alt:12.3f} km")
    
    # Calculate GMST
    gmst = calculate_gmst(sat.epoch_year, sat.epoch_day)
    print(f"\nGMST: {gmst * 180/PI:.4f}°")
    
    # Convert to geodetic
    lat, lon, alt = sat.eci_to_geodetic(x, y, z, gmst)
    print(f"\nGeodetic Position:")
    print(f"  Latitude:  {lat * 180/PI:8.4f}°")
    print(f"  Longitude: {lon * 180/PI:8.4f}°")
    print(f"  Altitude:  {alt:8.2f} km")
    
    # Propagate 90 minutes (one orbit)
    print(f"\nPosition at t=90 minutes:")
    x, y, z = sat.propagate(90.0)
    print(f"  X: {x:12.3f} km")
    print(f"  Y: {y:12.3f} km")
    print(f"  Z: {z:12.3f} km")
    
    r = math.sqrt(x*x + y*y + z*z)
    alt = r - XKMPER
    print(f"  Altitude: {alt:12.3f} km")
    
    # Show ground track
    print(f"\n" + "=" * 70)
    print("Ground Track Sample (every 15 minutes)")
    print("=" * 70)
    print(f"\n{'Time':>6} {'Latitude':>10} {'Longitude':>10} {'Altitude':>10}")
    print(f"{'(min)':>6} {'(deg)':>10} {'(deg)':>10} {'(km)':>10}")
    print("-" * 50)
    
    for t in range(0, 120, 15):
        x, y, z = sat.propagate(float(t))
        
        # Update GMST for current time
        day_offset = t / 1440.0
        gmst_curr = calculate_gmst(sat.epoch_year, sat.epoch_day + day_offset)
        
        lat, lon, alt = sat.eci_to_geodetic(x, y, z, gmst_curr)
        
        print(f"{t:6d} {lat*180/PI:10.4f} {lon*180/PI:10.4f} {alt:10.2f}")
    
    print("\n" + "=" * 70)
    print("Interface is 100% compatible with SGP4 class!")
    print("=" * 70)
