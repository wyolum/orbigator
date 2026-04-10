"""
observer_frame.py - Observer Reference Frame
=============================================
Computes station ECEF position and local East/North/Up unit vectors
once at startup. Provides cheap dot-product horizon test (hot loop safe)
and full az/el computation (alert mode only).

All ECEF coordinates in km, matching satellite_position.py output.
"""

import math

# WGS-84 constants (km)
_a  = 6378.137          # semi-major axis
_f  = 1.0 / 298.257223563
_e2 = 2 * _f - _f * _f  # eccentricity squared


class ObserverFrame:
    """
    Station reference frame precomputed at init.

    Parameters
    ----------
    lat_deg : float   geodetic latitude  (+N)
    lon_deg : float   geodetic longitude (+E)
    alt_km  : float   altitude above WGS-84 ellipsoid (default 0)
    """

    def __init__(self, lat_deg, lon_deg, alt_km=0.0):
        lat = math.radians(lat_deg)
        lon = math.radians(lon_deg)

        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        sin_lon = math.sin(lon)
        cos_lon = math.cos(lon)

        # Normal radius of curvature
        N = _a / math.sqrt(1.0 - _e2 * sin_lat * sin_lat)

        # Station ECEF (km)
        self.ox = (N + alt_km) * cos_lat * cos_lon
        self.oy = (N + alt_km) * cos_lat * sin_lon
        self.oz = (N * (1.0 - _e2) + alt_km) * sin_lat

        # Local East unit vector  (-sin_lon, cos_lon, 0)
        self.ex = -sin_lon
        self.ey =  cos_lon
        self.ez =  0.0

        # Local North unit vector  (-sin_lat*cos_lon, -sin_lat*sin_lon, cos_lat)
        self.nx = -sin_lat * cos_lon
        self.ny = -sin_lat * sin_lon
        self.nz =  cos_lat

        # Local Up unit vector  (cos_lat*cos_lon, cos_lat*sin_lon, sin_lat)
        self.ux = cos_lat * cos_lon
        self.uy = cos_lat * sin_lon
        self.uz = sin_lat

        self.lat_deg = lat_deg
        self.lon_deg = lon_deg

    # ------------------------------------------------------------------
    # HOT LOOP: trig-free horizon test
    #   6 multiplies + 3 adds + 1 comparison
    # ------------------------------------------------------------------
    def dot_up(self, sx, sy, sz):
        """
        Dot product of (sat - station) with local Up unit vector.
        Returns > 0 when satellite is above the geometric horizon,
                < 0 when below.
        No trig. Safe to call every tracking tick.
        """
        rx = sx - self.ox
        ry = sy - self.oy
        rz = sz - self.oz
        return rx * self.ux + ry * self.uy + rz * self.uz

    # ------------------------------------------------------------------
    # ALERT MODE ONLY: full ENU → az/el  (called ≤2 Hz)
    # ------------------------------------------------------------------
    def az_el_deg(self, sx, sy, sz):
        """
        Compute azimuth and elevation of satellite from observer.
        Returns (azimuth_deg, elevation_deg).
        Azimuth: 0=N, 90=E.  Elevation: 0=horizon, 90=zenith.
        """
        rx = sx - self.ox
        ry = sy - self.oy
        rz = sz - self.oz

        # Project onto ENU
        e_comp = rx * self.ex + ry * self.ey + rz * self.ez
        n_comp = rx * self.nx + ry * self.ny + rz * self.nz
        u_comp = rx * self.ux + ry * self.uy + rz * self.uz

        horiz = math.sqrt(e_comp * e_comp + n_comp * n_comp)

        el_rad = math.atan2(u_comp, horiz)
        az_rad = math.atan2(e_comp, n_comp)   # atan2(E, N) = bearing from N

        az_deg = math.degrees(az_rad) % 360.0
        el_deg = math.degrees(el_rad)

        return az_deg, el_deg
