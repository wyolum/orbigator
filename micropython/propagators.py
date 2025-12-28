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
        if not self._sgp4_mod:
            return 0.0, 0.0
        
        # Calculate time since TLE epoch
        jd_now = utils.get_jd(unix_time)
        jd_epoch = utils.get_jd_of_tle_epoch(self.sgp4.epoch_year, self.sgp4.epoch_day)
        t_min = (jd_now - jd_epoch) * 1440.0
        
        # print(f"DEBUG SGP4: JD_Now={jd_now:.4f} Epoch={jd_epoch:.4f} t_min={t_min:.4f}")
        
        # Propagate
        x, y, z = self.sgp4.propagate(t_min)
        gmst = utils.compute_gmst(unix_time)
        lat, lon, alt = self.sgp4.eci_to_geodetic(x, y, z, gmst)
        
        self.last_alt = alt
        
        # Map to motor angles
        # AoV = Latitude (-90 to +90 -> 0 to 180)
        # EQX = Longitude (-180 to +180 -> 0 to 360)
        aov_deg = math.degrees(lat) + 90.0
        eqx_deg = math.degrees(lon) + 180.0
        
        return aov_deg, eqx_deg

    def get_altitude(self):
        return self.last_alt
