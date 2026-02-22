"""
Orbital Propagators for Orbigator.
Abstracts the mathematical models for satellite tracking/simulation.
"""

import math
import time
import orb_utils as utils
import orb_globals as g

class Propagate:
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

class KeplerJ2(Propagate):
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
        """
        Calculates motor angles using High-Precision Periodic Time Reduction.
        This preserves 32-bit float precision by keeping elapsed time within one period.
        """
        # Calculate elapsed time within a single period to avoid float precision loss.
        # (unix_time % period - start_time % period) % period
        aov_elapsed = (unix_time % self.period_sec - self.start_time % self.period_sec) % self.period_sec

        # Earth rotation period is ~86400s
        eqx_period = 360.0 / abs(self.eqx_rate) if self.eqx_rate != 0 else 86400.0
        eqx_elapsed = (unix_time % eqx_period - self.start_time % eqx_period) % eqx_period

        # AoV Position
        if self.eccentricity > 0.001:
            aov_pos, _ = utils.compute_elliptical_position(
                aov_elapsed, self.period_sec, self.eccentricity, self.periapsis_deg
            )
            aov_deg = self.start_aov + aov_pos
        else:
            aov_deg = self.start_aov + (self.aov_rate * aov_elapsed)

        # EQX Position (Constant velocity)
        eqx_deg = self.start_eqx + (self.eqx_rate * eqx_elapsed)

        return aov_deg, eqx_deg

    def get_altitude(self):
        return self.altitude_km

    def nudge_aov(self, delta_deg):
        self.start_aov += delta_deg

    def nudge_eqx(self, delta_deg):
        self.start_eqx += delta_deg

class MicroSGP4(Propagate):
    """
    SGP4 propagator using TLE data.
    Delegates orbital math to sgp4.py — reads orbital elements
    (_raan_curr, _argp_curr, _nu) exposed after propagation.
    """
    def __init__(self, sgp4_model):
        self.sgp4 = sgp4_model
        self.last_alt = 0.0
        self.last_ecef = None   # (x_km, y_km, z_km) — updated in get_aov_eqx()
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

        try:
            import satellite_position

            import time
            t_struct = time.gmtime(unix_time)
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

            # Cache ECEF for observer_frame dot test
            ecef = result.get('ecef', {})
            self.last_ecef = (ecef.get('x', 0.0), ecef.get('y', 0.0), ecef.get('z', 0.0))

            # Store altitude for retrieval
            self.last_alt = alt_km

            # sgp4.propagate() already computed and stored orbital elements.
            # Call it to ensure elements are current for this t_min.
            self.sgp4.propagate(t_min)

            # Read orbital elements directly from sgp4 instance
            aov_deg = math.degrees(self.sgp4._nu + self.sgp4._argp_curr) % 360.0
            eqx_deg = math.degrees(self.sgp4._raan_curr - gmst) % 360.0

            return aov_deg, eqx_deg, lat_deg, lon_deg

        except ImportError:
            print("SGP4 Error: satellite_position module missing")
            return 0.0, 0.0, 0.0, 0.0
        except Exception as e:
            print(f"SGP4 Prop Error: {e}")
            return 0.0, 0.0, 0.0, 0.0

    def get_altitude(self):
        return self.last_alt

    def get_ecef(self):
        """Return cached (x, y, z) ECEF km from last propagation, or None."""
        return self.last_ecef
