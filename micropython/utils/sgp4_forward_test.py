"""
SGP4 Forward Propagation Test
Compares simplified SGP4 implementation against python-sgp4 reference
at multiple time offsets from TLE epoch.

Tests two error sources independently:
  1) SGP4 propagation error (ECI position difference)
  2) Coordinate conversion error (GMST/ECEF/geodetic pipeline)

Copies all code inline to avoid import conflicts with pip sgp4.
"""

import math
import calendar
import time as _time

# ── Reference implementation (pip sgp4) ──────────────────────────────
from sgp4.api import Satrec, jday

# ── ISS TLE from test_sgp4.py ────────────────────────────────────────
line1 = "1 25544U 98067A   25359.56752749  .00014081  00000-0  25591-3 0  9998"
line2 = "2 25544  51.6318  78.9495 0003224 299.9641  60.1027 15.49813539544848"

# =====================================================================
# VERBATIM COPY of sgp4.py constants and class
# =====================================================================

# WGS-72 Constants
CK2   = 5.413080e-4
CK4   = 6.2098875e-7
E6A   = 1.0e-6
QOMS2T = 1.88027916e-9
S     = 1.01222928e-2
XJ3   = -2.53881e-6
XKE   = 7.43669161e-2
XKMPER = 6378.135
XMNPDA = 1440.0
AE    = 1.0
DE2RA = 0.0174532925199433
PI    = 3.14159265358979323846
PIO2  = 1.57079632679489656
TWOPI = 6.283185307179586
X3PIO2 = 4.71238898038469


class SGP4:
    def __init__(self):
        pass

    def init(self, epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n):
        self.epoch_year = epoch_year
        self.epoch_day = epoch_day
        self.bstar = bstar
        self.inc = inc * DE2RA
        self.raan = raan * DE2RA
        self.ecc = ecc
        self.argp = argp * DE2RA
        self.m = m * DE2RA
        self.n = n * TWOPI / 1440.0  # revs/day -> rad/min

        # Recover semi-major axis (aodp)
        a1 = math.pow(XKE / self.n, 2.0/3.0)
        cosio = math.cos(self.inc)
        theta2 = cosio * cosio
        x3thm1 = 3.0 * theta2 - 1.0
        eosq = self.ecc * self.ecc
        betao2 = 1.0 - eosq
        betao = math.sqrt(betao2)
        del1 = 1.5 * CK2 * x3thm1 / (a1 * a1 * betao * betao2)
        ao = a1 * (1.0 - del1 * (0.5 * TWOPI / (a1 * a1 * betao * betao2) * 1.5 * CK2 * x3thm1 + del1 * del1 / 3.0 + 1.0))
        delo = 1.5 * CK2 * x3thm1 / (ao * ao * betao * betao2)
        self.aodp = a1 * (1.0 - delo)
        self.xnodp = self.n / (1.0 + delo)

        # Init constants
        self.sinio = math.sin(self.inc)
        self.cosio = cosio
        self.x3thm1 = x3thm1

        # Calculate proper secular rates (J2 perturbations)
        # RAAN precession rate
        self.xnodot = -1.5 * CK2 * self.cosio / (self.aodp * self.aodp * betao2 * betao2) * self.xnodp

        # Argument of perigee precession rate
        self.omgdot = 0.75 * CK2 * (5.0 * theta2 - 1.0) / (self.aodp * self.aodp * betao2 * betao2) * self.xnodp

        # Mean motion rate (corrected for drag)
        self.xmdot = self.xnodp

    def propagate(self, t_min):
        # Update Mean Anomaly
        m_curr = (self.m + self.xmdot * t_min) % TWOPI

        # Update RAAN using pre-calculated rate
        raan_curr = (self.raan + self.xnodot * t_min) % TWOPI

        # Update Arg Perigee using pre-calculated rate
        argp_curr = (self.argp + self.omgdot * t_min) % TWOPI

        # Solve Kepler's Equation
        e_anom = m_curr
        for i in range(10):
            d_e = (m_curr - e_anom + self.ecc * math.sin(e_anom)) / (1.0 - self.ecc * math.cos(e_anom))
            e_anom += d_e
            if abs(d_e) < 1e-6:
                break

        # True Anomaly
        sin_e = math.sin(e_anom)
        cos_e = math.cos(e_anom)
        nu = math.atan2(math.sqrt(1.0 - self.ecc * self.ecc) * sin_e, cos_e - self.ecc)

        # Radial distance
        r = self.aodp * (1.0 - self.ecc * cos_e)

        # Arg Latitude
        u = argp_curr + nu

        # Position in orbital plane
        x_prime = r * math.cos(u)
        y_prime = r * math.sin(u)

        # Rotate to ECI
        cos_raan = math.cos(raan_curr)
        sin_raan = math.sin(raan_curr)
        cos_inc = math.cos(self.inc)
        sin_inc = math.sin(self.inc)

        x = (x_prime * cos_raan - y_prime * cos_inc * sin_raan) * XKMPER
        y = (x_prime * sin_raan + y_prime * cos_inc * cos_raan) * XKMPER
        z = (y_prime * sin_inc) * XKMPER

        return (x, y, z)

    def eci_to_geodetic(self, x, y, z, gmst):
        r = math.sqrt(x*x + y*y)
        lon = math.atan2(y, x) + gmst  # Changed from - to +

        while lon > PI:
            lon -= TWOPI
        while lon < -PI:
            lon += TWOPI

        lat = math.atan2(z, r)
        phi = lat
        a = 6378.137
        f = 1.0 / 298.257223563
        e2 = 2*f - f*f

        for i in range(5):
            sin_phi = math.sin(phi)
            c = a / math.sqrt(1.0 - e2 * sin_phi * sin_phi)
            phi = math.atan2(z + c * e2 * sin_phi, r)

        alt = r / math.cos(phi) - c
        return (phi, lon, alt)  # Radians, Radians, km


# =====================================================================
# VERBATIM COPY of satellite_position.py functions
# (with time.mktime -> calendar.timegm, time.gmtime -> not used)
# =====================================================================

def compute_julian_date(year, month, day, hour=0, minute=0, second=0):
    """Compute Julian Date from calendar date."""
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    jd += (hour + (minute + second / 60.0) / 60.0) / 24.0
    return jd


def gmst_from_unix(unix_timestamp):
    """Calculate Greenwich Mean Sidereal Time from Unix timestamp."""
    J2000_UNIX = 946728000
    s_since_j2000 = int(unix_timestamp) - J2000_UNIX
    d_int = s_since_j2000 // 86400
    s_rem = s_since_j2000 % 86400
    d_frac = s_rem / 86400.0
    d = d_int + d_frac
    gmst_deg = (280.46061837 + 360.98564736629 * d) % 360.0
    return math.radians(gmst_deg)


def eci_to_ecef(x_eci, y_eci, z_eci, gmst):
    """Convert ECI coordinates to ECEF (Earth-Centered Earth-Fixed)"""
    cos_gmst = math.cos(gmst)
    sin_gmst = math.sin(gmst)
    x_ecef = cos_gmst * x_eci + sin_gmst * y_eci
    y_ecef = -sin_gmst * x_eci + cos_gmst * y_eci
    z_ecef = z_eci
    return x_ecef, y_ecef, z_ecef


def ecef_to_geodetic(x, y, z):
    """Convert ECEF coordinates to geodetic (lat, lon, alt) using WGS-84"""
    a = 6378.137
    f = 1.0 / 298.257223563
    e2 = 2*f - f*f

    lon = math.atan2(y, x)
    p = math.sqrt(x*x + y*y)
    lat = math.atan2(z, p * (1.0 - e2))

    for _ in range(5):
        sin_lat = math.sin(lat)
        N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
        alt = p / math.cos(lat) - N
        lat = math.atan2(z, p * (1.0 - e2 * N / (N + alt)))

    sin_lat = math.sin(lat)
    N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - N
    return math.degrees(lat), math.degrees(lon), alt


def compute_satellite_geodetic(sgp4_obj, tle_epoch_year, tle_epoch_day, current_time_tuple=None):
    """
    Compute satellite geodetic position from SGP4 object.
    Adapted: uses calendar.timegm instead of time.mktime.
    """
    if current_time_tuple is None:
        t = _time.gmtime()
        current_time_tuple = (t[0], t[1], t[2], t[3], t[4], t[5])

    # Pad tuple to 9 elements for timegm
    if len(current_time_tuple) < 9:
        tmp = list(current_time_tuple)
        while len(tmp) < 9:
            tmp.append(0)
        current_time_tuple = tuple(tmp)

    # calendar.timegm gives Unix epoch (UTC), replacing time.mktime (local time)
    unix_now = calendar.timegm(current_time_tuple)

    # Compute Unix timestamp for TLE epoch
    year = tle_epoch_year
    if year < 100:
        year += 2000

    epoch_jan1_jd = compute_julian_date(year, 1, 1, 0, 0, 0)
    epoch_jan1_unix = int((epoch_jan1_jd - 2440587.5) * 86400.0)
    epoch_unix = epoch_jan1_unix + int((tle_epoch_day - 1.0) * 86400.0)

    t_min = (int(unix_now) - epoch_unix) / 60.0

    x_eci, y_eci, z_eci = sgp4_obj.propagate(t_min)
    gmst = gmst_from_unix(unix_now)
    x_ecef, y_ecef, z_ecef = eci_to_ecef(x_eci, y_eci, z_eci, gmst)
    lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)

    return {
        'latitude': lat,
        'longitude': lon,
        'altitude': alt,
        't_min': t_min,
        'eci': {'x': x_eci, 'y': y_eci, 'z': z_eci},
        'ecef': {'x': x_ecef, 'y': y_ecef, 'z': z_ecef},
        'gmst': gmst,
    }


# =====================================================================
# Helper: convert TLE epoch to a datetime-like tuple (year,mo,day,h,m,s)
# =====================================================================

def tle_epoch_to_tuple(epoch_year_4d, epoch_day):
    """Return (year, month, day, hour, minute, second) from TLE epoch."""
    from datetime import datetime, timedelta
    base = datetime(epoch_year_4d, 1, 1) + timedelta(days=epoch_day - 1.0)
    return (base.year, base.month, base.day, base.hour, base.minute, base.second)


def add_minutes_to_tuple(tup, minutes):
    """Add minutes to a (Y,M,D,h,m,s) tuple, return new tuple."""
    from datetime import datetime, timedelta
    dt = datetime(*tup) + timedelta(minutes=minutes)
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


# =====================================================================
# Parse TLE
# =====================================================================

def parse_tle():
    epoch_year = int(line1[18:20])
    if epoch_year < 57:
        epoch_year_4d = epoch_year + 2000
    else:
        epoch_year_4d = epoch_year + 1900

    epoch_day = float(line1[20:32])
    bstar = float(line1[53:59]) * 10.0 ** float(line1[59:61])
    inc = float(line2[8:16])
    raan = float(line2[17:25])
    ecc = float('0.' + line2[26:33])
    argp = float(line2[34:42])
    ma = float(line2[43:51])
    n = float(line2[52:63])

    return epoch_year, epoch_year_4d, epoch_day, bstar, inc, raan, ecc, argp, ma, n


# =====================================================================
# MAIN
# =====================================================================

def main():
    epoch_year, epoch_year_4d, epoch_day, bstar, inc, raan, ecc, argp, ma, n = parse_tle()

    # Initialize our simplified SGP4
    our_sgp4 = SGP4()
    our_sgp4.init(epoch_year_4d, epoch_day, bstar, inc, raan, ecc, argp, ma, n)

    # Initialize reference SGP4
    ref_sat = Satrec.twoline2rv(line1, line2)

    # Epoch as a calendar tuple
    epoch_tuple = tle_epoch_to_tuple(epoch_year_4d, epoch_day)

    # Test offsets in minutes from TLE epoch
    t_offsets = [0, 60, 360, 720, 1440]

    print("=" * 100)
    print("SGP4 FORWARD PROPAGATION TEST")
    print("=" * 100)
    print(f"TLE: ISS (NORAD 25544)")
    print(f"Epoch: {epoch_year_4d}-{epoch_day:.8f} => {epoch_tuple}")
    print()

    # ─────────────────────────────────────────────────────────────────
    # TEST 1: Pure SGP4 propagation (ECI comparison)
    # ─────────────────────────────────────────────────────────────────
    print("=" * 100)
    print("TEST 1: SGP4 Propagation — ECI Position Comparison")
    print("=" * 100)
    header = f"{'t_min':>7} | {'Our X':>12} {'Our Y':>12} {'Our Z':>12} | {'Ref X':>12} {'Ref Y':>12} {'Ref Z':>12} | {'dX':>8} {'dY':>8} {'dZ':>8} {'|dR|':>8}"
    print(header)
    print("-" * len(header))

    eci_results = {}  # store for later use

    for t_min in t_offsets:
        # Our implementation
        ox, oy, oz = our_sgp4.propagate(t_min)

        # Reference: need jday at epoch + t_min
        target_tuple = add_minutes_to_tuple(epoch_tuple, t_min)
        jd, fr = jday(target_tuple[0], target_tuple[1], target_tuple[2],
                       target_tuple[3], target_tuple[4], target_tuple[5])
        err, ref_r, ref_v = ref_sat.sgp4(jd, fr)
        if err != 0:
            print(f"{t_min:>7} | Reference SGP4 error code {err}")
            continue

        rx, ry, rz = ref_r
        dx = ox - rx
        dy = oy - ry
        dz = oz - rz
        dr = math.sqrt(dx*dx + dy*dy + dz*dz)

        eci_results[t_min] = {
            'our': (ox, oy, oz),
            'ref': (rx, ry, rz),
            'dr': dr,
            'target_tuple': target_tuple,
        }

        print(f"{t_min:>7} | {ox:>12.2f} {oy:>12.2f} {oz:>12.2f} | {rx:>12.2f} {ry:>12.2f} {rz:>12.2f} | {dx:>+8.2f} {dy:>+8.2f} {dz:>+8.2f} {dr:>8.2f}")

    print()

    # ─────────────────────────────────────────────────────────────────
    # TEST 2: Full pipeline lat/lon comparison
    #   - Our pipeline:  our SGP4 -> our GMST -> our ECEF -> our geodetic
    #   - Ref pipeline:  ref SGP4 -> same GMST -> same ECEF -> same geodetic
    # ─────────────────────────────────────────────────────────────────
    print("=" * 100)
    print("TEST 2: Full Pipeline — Lat/Lon Comparison (our SGP4 vs reference SGP4, same coord conversion)")
    print("=" * 100)
    header2 = f"{'t_min':>7} | {'Our Lat':>9} {'Our Lon':>9} {'Our Alt':>9} | {'Ref Lat':>9} {'Ref Lon':>9} {'Ref Alt':>9} | {'dLat':>8} {'dLon':>8} {'dAlt':>8}"
    print(header2)
    print("-" * len(header2))

    for t_min in t_offsets:
        if t_min not in eci_results:
            continue
        info = eci_results[t_min]
        tt = info['target_tuple']

        # Compute Unix timestamp for this time
        padded = list(tt) + [0, 0, 0] if len(tt) < 9 else list(tt)
        while len(padded) < 9:
            padded.append(0)
        unix_ts = calendar.timegm(tuple(padded))

        # GMST (shared by both pipelines)
        gmst = gmst_from_unix(unix_ts)

        # --- Our pipeline ---
        ox, oy, oz = info['our']
        o_xecef, o_yecef, o_zecef = eci_to_ecef(ox, oy, oz, gmst)
        o_lat, o_lon, o_alt = ecef_to_geodetic(o_xecef, o_yecef, o_zecef)

        # --- Reference pipeline (ref ECI -> same coord conversion) ---
        rx, ry, rz = info['ref']
        r_xecef, r_yecef, r_zecef = eci_to_ecef(rx, ry, rz, gmst)
        r_lat, r_lon, r_alt = ecef_to_geodetic(r_xecef, r_yecef, r_zecef)

        d_lat = o_lat - r_lat
        d_lon = o_lon - r_lon
        if d_lon > 180:
            d_lon -= 360
        elif d_lon < -180:
            d_lon += 360
        d_alt = o_alt - r_alt

        print(f"{t_min:>7} | {o_lat:>+9.3f} {o_lon:>+9.3f} {o_alt:>9.1f} | {r_lat:>+9.3f} {r_lon:>+9.3f} {r_alt:>9.1f} | {d_lat:>+8.3f} {d_lon:>+8.3f} {d_alt:>+8.1f}")

    print()

    # ─────────────────────────────────────────────────────────────────
    # TEST 3: Coordinate conversion test
    #   Feed SAME reference ECI into:
    #     a) our eci_to_ecef + ecef_to_geodetic pipeline
    #     b) SGP4 class eci_to_geodetic method (from sgp4.py)
    #   to see if coordinate conversion itself introduces error.
    # ─────────────────────────────────────────────────────────────────
    print("=" * 100)
    print("TEST 3: Coordinate Conversion Isolation — Same Reference ECI through different pipelines")
    print("=" * 100)
    print("Pipeline A: eci_to_ecef() + ecef_to_geodetic()  [satellite_position.py]")
    print("Pipeline B: SGP4.eci_to_geodetic()              [sgp4.py method]")
    print()
    header3 = f"{'t_min':>7} | {'PipeA Lat':>10} {'PipeA Lon':>10} | {'PipeB Lat':>10} {'PipeB Lon':>10} | {'dLat':>8} {'dLon':>8}"
    print(header3)
    print("-" * len(header3))

    for t_min in t_offsets:
        if t_min not in eci_results:
            continue
        info = eci_results[t_min]
        tt = info['target_tuple']

        padded = list(tt)
        while len(padded) < 9:
            padded.append(0)
        unix_ts = calendar.timegm(tuple(padded))
        gmst = gmst_from_unix(unix_ts)

        rx, ry, rz = info['ref']

        # Pipeline A: satellite_position.py style
        xecef, yecef, zecef = eci_to_ecef(rx, ry, rz, gmst)
        a_lat, a_lon, a_alt = ecef_to_geodetic(xecef, yecef, zecef)

        # Pipeline B: sgp4.py eci_to_geodetic method
        b_phi, b_lon_rad, b_alt = our_sgp4.eci_to_geodetic(rx, ry, rz, gmst)
        b_lat = math.degrees(b_phi)
        b_lon = math.degrees(b_lon_rad)

        d_lat = a_lat - b_lat
        d_lon = a_lon - b_lon
        if d_lon > 180:
            d_lon -= 360
        elif d_lon < -180:
            d_lon += 360

        print(f"{t_min:>7} | {a_lat:>+10.4f} {a_lon:>+10.4f} | {b_lat:>+10.4f} {b_lon:>+10.4f} | {d_lat:>+8.4f} {d_lon:>+8.4f}")

    print()

    # ─────────────────────────────────────────────────────────────────
    # TEST 4: Full satellite_position pipeline test
    #   Uses compute_satellite_geodetic() — the EXACT code path the device uses
    #   (with calendar.timegm instead of time.mktime)
    # ─────────────────────────────────────────────────────────────────
    print("=" * 100)
    print("TEST 4: Full compute_satellite_geodetic() pipeline vs reference")
    print("=" * 100)
    header4 = f"{'t_min':>7} | {'Our Lat':>9} {'Our Lon':>9} {'Our Alt':>9} {'Our tmin':>10} | {'Ref Lat':>9} {'Ref Lon':>9} | {'dLat':>8} {'dLon':>8}"
    print(header4)
    print("-" * len(header4))

    for t_min in t_offsets:
        if t_min not in eci_results:
            continue
        info = eci_results[t_min]
        tt = info['target_tuple']

        # Use compute_satellite_geodetic with explicit time tuple
        result = compute_satellite_geodetic(our_sgp4, epoch_year_4d, epoch_day,
                                            current_time_tuple=tt)

        # Reference lat/lon (ref SGP4 + our coord conversion)
        rx, ry, rz = info['ref']
        padded = list(tt)
        while len(padded) < 9:
            padded.append(0)
        unix_ts = calendar.timegm(tuple(padded))
        gmst = gmst_from_unix(unix_ts)
        r_xecef, r_yecef, r_zecef = eci_to_ecef(rx, ry, rz, gmst)
        r_lat, r_lon, r_alt = ecef_to_geodetic(r_xecef, r_yecef, r_zecef)

        d_lat = result['latitude'] - r_lat
        d_lon = result['longitude'] - r_lon
        if d_lon > 180:
            d_lon -= 360
        elif d_lon < -180:
            d_lon += 360

        print(f"{t_min:>7} | {result['latitude']:>+9.3f} {result['longitude']:>+9.3f} {result['altitude']:>9.1f} {result['t_min']:>10.2f} | {r_lat:>+9.3f} {r_lon:>+9.3f} | {d_lat:>+8.3f} {d_lon:>+8.3f}")

    print()

    # ─────────────────────────────────────────────────────────────────
    # TEST 5: Bug in sgp4.py eci_to_geodetic — GMST sign
    #   The sgp4.py method has lon = atan2(y,x) + gmst
    #   Correct should be lon = atan2(y,x) - gmst
    #   Let's show the difference.
    # ─────────────────────────────────────────────────────────────────
    print("=" * 100)
    print("TEST 5: GMST Sign Check — sgp4.py eci_to_geodetic uses +gmst; correct is -gmst")
    print("=" * 100)
    header5 = f"{'t_min':>7} | {'GMST deg':>10} | {'+gmst Lon':>10} {'-gmst Lon':>10} {'Correct':>10} | {'Err(+)':>8} {'Err(-)':>8}"
    print(header5)
    print("-" * len(header5))

    for t_min in t_offsets:
        if t_min not in eci_results:
            continue
        info = eci_results[t_min]
        tt = info['target_tuple']

        padded = list(tt)
        while len(padded) < 9:
            padded.append(0)
        unix_ts = calendar.timegm(tuple(padded))
        gmst = gmst_from_unix(unix_ts)

        rx, ry, rz = info['ref']

        # Method with +gmst (sgp4.py style)
        r_xy = math.sqrt(rx*rx + ry*ry)
        lon_plus = math.atan2(ry, rx) + gmst
        while lon_plus > PI:
            lon_plus -= TWOPI
        while lon_plus < -PI:
            lon_plus += TWOPI

        # Method with -gmst (standard)
        lon_minus = math.atan2(ry, rx) - gmst
        while lon_minus > PI:
            lon_minus -= TWOPI
        while lon_minus < -PI:
            lon_minus += TWOPI

        # Correct: via ECEF rotation
        r_xecef, r_yecef, r_zecef = eci_to_ecef(rx, ry, rz, gmst)
        _, correct_lon, _ = ecef_to_geodetic(r_xecef, r_yecef, r_zecef)

        err_plus = math.degrees(lon_plus) - correct_lon
        if err_plus > 180:
            err_plus -= 360
        elif err_plus < -180:
            err_plus += 360

        err_minus = math.degrees(lon_minus) - correct_lon
        if err_minus > 180:
            err_minus -= 360
        elif err_minus < -180:
            err_minus += 360

        print(f"{t_min:>7} | {math.degrees(gmst):>10.3f} | {math.degrees(lon_plus):>+10.3f} {math.degrees(lon_minus):>+10.3f} {correct_lon:>+10.3f} | {err_plus:>+8.3f} {err_minus:>+8.3f}")

    print()

    # ─────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print()

    max_dr = 0
    max_dlat = 0
    max_dlon = 0
    for t_min in t_offsets:
        if t_min not in eci_results:
            continue
        info = eci_results[t_min]
        tt = info['target_tuple']

        padded = list(tt)
        while len(padded) < 9:
            padded.append(0)
        unix_ts = calendar.timegm(tuple(padded))
        gmst = gmst_from_unix(unix_ts)

        ox, oy, oz = info['our']
        rx, ry, rz = info['ref']
        dr = info['dr']
        if dr > max_dr:
            max_dr = dr

        # Our full pipeline
        o_xecef, o_yecef, o_zecef = eci_to_ecef(ox, oy, oz, gmst)
        o_lat, o_lon, _ = ecef_to_geodetic(o_xecef, o_yecef, o_zecef)

        # Ref full pipeline
        r_xecef, r_yecef, r_zecef = eci_to_ecef(rx, ry, rz, gmst)
        r_lat, r_lon, _ = ecef_to_geodetic(r_xecef, r_yecef, r_zecef)

        d_lat = abs(o_lat - r_lat)
        d_lon = abs(o_lon - r_lon)
        if d_lon > 180:
            d_lon = 360 - d_lon
        if d_lat > max_dlat:
            max_dlat = d_lat
        if d_lon > max_dlon:
            max_dlon = d_lon

    print(f"Max ECI position error:     {max_dr:>10.2f} km")
    print(f"Max latitude error:         {max_dlat:>10.3f} deg")
    print(f"Max longitude error:        {max_dlon:>10.3f} deg")
    print()
    print("Error sources identified:")
    print("  1) SGP4 propagation: simplified model omits drag (bstar), higher-order")
    print("     J2/J3/J4 perturbations, deep-space terms, atmospheric drag decay.")
    print("     Error grows with propagation time.")
    print("  2) sgp4.py eci_to_geodetic uses lon = atan2(y,x) + gmst instead of -gmst.")
    print("     This adds 2*GMST to longitude (~2 * GMST degrees error).")
    print("  3) satellite_position.py eci_to_ecef + ecef_to_geodetic is correct")
    print("     (subtracts Earth rotation properly via ECEF matrix).")
    print()
    print("The user-reported ~24 deg lat / ~29 deg lon error is consistent with")
    print("the SGP4 propagation error growing over time (no drag model).")
    print("If the device uses sgp4.py's eci_to_geodetic, longitude also has the +gmst bug.")


if __name__ == "__main__":
    main()
