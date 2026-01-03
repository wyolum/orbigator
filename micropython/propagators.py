"""
Orbital Propagators for Orbigator.
Abstracts the mathematical models for satellite tracked/simulation.
"""

import math
import time
import orb_utils as utils
import orb_globals as g

class Propagator:
    """Base class for all orbital propagators."""
    def get_aov_eqx(self, unix_time):
        """
        Calculate AoV and EQX angles for a given unix timestamp.
        Returns (aov_deg, eqx_deg).
        """
        raise NotImplementedError

    def get_altitude(self):
        """Current altitude in km."""
        return 0.0

    def nudge_aov(self, delta_deg):
        """Adjust AoV phase by delta_deg."""
        pass
        
    def nudge_eqx(self, delta_deg):
        """Adjust EQX phase by delta_deg."""
        pass

class KeplerPropagator(Propagator):
    """
    Standard Keplerian propagator for manual orbits.
    Supports circular and elliptical paths.
    """
    def __init__(self, altitude_km, inclination_deg, eccentricity, periapsis_deg, 
                 start_aov, start_eqx, start_time):
        self.altitude_km = altitude_km
        self.inclination_deg = inclination_deg
        self.eccentricity = eccentricity
        self.periapsis_deg = periapsis_deg
        
        self.start_aov = start_aov
        self.start_eqx = start_eqx
        self.start_time = start_time # Unix timestamp
        
        # Pre-calculate rates for circular case
        aov_rate, eqx_rate_sec, _, period_min = utils.compute_motor_rates(altitude_km)
        self.aov_rate = aov_rate
        self.eqx_rate = eqx_rate_sec
        self.period_sec = period_min * 60.0

    def get_aov_eqx(self, unix_time):
        elapsed = unix_time - self.start_time
        
        # AoV Position
        if self.eccentricity > 0.001:
            aov_pos, _ = utils.compute_elliptical_position(
                elapsed, self.period_sec, self.eccentricity, self.periapsis_deg
            )
            aov_deg = self.start_aov + aov_pos
        else:
            aov_deg = self.start_aov + (self.aov_rate * elapsed)
            
        # EQX Position (Constant velocity)
        eqx_deg = self.start_eqx + (self.eqx_rate * elapsed)
        
        return aov_deg, eqx_deg

    def get_altitude(self):
        return self.altitude_km

    def nudge_aov(self, delta_deg):
        self.start_aov += delta_deg
        
    def nudge_eqx(self, delta_deg):
        self.start_eqx += delta_deg

class SGP4Propagator(Propagator):
    """
    SGP4 propagator using TLE data.
    """
    def __init__(self, sgp4_model):
        self.sgp4 = sgp4_model
        self.last_alt = 0.0
        # Cache for performance
        try:
            import sgp4
            self._sgp4_mod = sgp4
        except ImportError:
            self._sgp4_mod = None

    def get_aov_eqx(self, unix_time):
        """
        Returns (aov_deg, eqx_deg, lat_deg, lon_deg)
        aov/eqx are the motor targets (orbital phase/RAAN)
        lat/lon are the geodetic ground track
        """
        if not self._sgp4_mod:
            return 0.0, 0.0, 0.0, 0.0
        
        # Access external satellite_position module for robust calculation
        # This module handles 32-bit float precision limitations on Pico 2W correctly
        try:
            import satellite_position
            
            # Helper to get current time from unix timestamp
            import time
            t_struct = time.gmtime(unix_time)
            # Ensure 9-tuple for compatibility
            t_tuple = (t_struct[0], t_struct[1], t_struct[2], t_struct[3], t_struct[4], t_struct[5], 0, 0, 0)
            
            result = satellite_position.compute_satellite_geodetic(
                self.sgp4, 
                self.sgp4.epoch_year, 
                self.sgp4.epoch_day, 
                t_tuple
            )
            
            lat_deg = result['latitude']
            lon_deg = result['longitude']
            alt_km = result['altitude']
            gmst = result['gmst']
            t_min = result.get('t_min', 0)
            
            # Store altitude for retrieval
            self.last_alt = alt_km
            
            # --- Continue with specific Orbigator motor mapping ---
            
            # 3. Update Orbital Elements with J2 Precession (high-precision)
            # We need t_min for this, which we now get from the robust calculation
            
            theta2 = self.sgp4.cosio * self.sgp4.cosio
            eosq = self.sgp4.ecc * self.sgp4.ecc
            betao2 = 1.0 - eosq
            CK2 = 5.413080e-4 
            
            # RAAN Precession
            rdot = -1.5 * CK2 * self.sgp4.cosio / (self.sgp4.aodp * self.sgp4.aodp * betao2 * betao2) * self.sgp4.n
            raan_curr = (self.sgp4.raan + rdot * t_min)
            
            # Arg of Perigee Precession
            pdot = 0.75 * CK2 * (5.0 * theta2 - 1.0) / (self.sgp4.aodp * self.sgp4.aodp * betao2 * betao2) * self.sgp4.n
            argp_curr = (self.sgp4.argp + pdot * t_min)
            
            # 4. Solve Kepler's Equation for True Anomaly (nu)
            m_curr = (self.sgp4.m + self.sgp4.xmdot * t_min)
            e_anom = m_curr
            for i in range(10):
                d_e = (m_curr - e_anom + self.sgp4.ecc * math.sin(e_anom)) / (1.0 - self.sgp4.ecc * math.cos(e_anom))
                e_anom += d_e
                if abs(d_e) < 1e-6: break
                
            sin_e = math.sin(e_anom)
            cos_e = math.cos(e_anom)
            nu = math.atan2(math.sqrt(1.0 - self.sgp4.ecc * self.sgp4.ecc) * sin_e, cos_e - self.sgp4.ecc)
            
            # 5. Map to Orbigator drive coordinates
            # AoV = Argument of Latitude (angle from ascending node) = nu + argp
            aov_deg = math.degrees(nu + argp_curr) % 360.0
            
            # EQX = Longitude of Ascending Node = RAAN - GMST
            # This represents the longitude where the orbit crosses the equator ascending (ECEF frame)
            # Since Earth rotates East, the node moves West (retrograde) relative to surface.
            eqx_deg = math.degrees(raan_curr - gmst) % 360.0
            
            return aov_deg, eqx_deg, lat_deg, lon_deg
            
        except ImportError:
            # Fallback if module missing (should not happen in prod)
            print("SGP4 Error: satellite_position module missing")
            return 0.0, 0.0, 0.0, 0.0
        except Exception as e:
            print(f"SGP4 Prop Error: {e}")
            return 0.0, 0.0, 0.0, 0.0

    def get_altitude(self):
        return self.last_alt
