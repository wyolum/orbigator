import math

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
        self.n = n * TWOPI / 1440.0 # revs/day -> rad/min

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
        
        # Simplified secular rates
        self.omgdot = 0.0 # Simplified
        self.xnodot = 0.0 # Simplified
        self.xmdot = self.xnodp # Simplified

    def propagate(self, t_min):
        # Update Mean Anomaly
        m_curr = self.m + self.xmdot * t_min
        
        # Update RAAN (J2 perturbation)
        theta2 = self.cosio * self.cosio
        x3thm1 = 3.0 * theta2 - 1.0
        eosq = self.ecc * self.ecc
        betao2 = 1.0 - eosq
        rdot = -1.5 * CK2 * self.cosio / (self.aodp * self.aodp * betao2 * betao2) * self.n
        raan_curr = self.raan + rdot * t_min
        
        # Update Arg Perigee
        pdot = 0.75 * CK2 * (5.0 * theta2 - 1.0) / (self.aodp * self.aodp * betao2 * betao2) * self.n
        argp_curr = self.argp + pdot * t_min

        # Solve Kepler's Equation
        e_anom = m_curr
        for i in range(10):
            d_e = (m_curr - e_anom + self.ecc * math.sin(e_anom)) / (1.0 - self.ecc * math.cos(e_anom))
            e_anom += d_e
            if abs(d_e) < 1e-6: break

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
        lon = math.atan2(y, x) - gmst
        
        while lon > PI: lon -= TWOPI
        while lon < -PI: lon += TWOPI
        
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
        return (phi, lon, alt) # Radians, Radians, km
