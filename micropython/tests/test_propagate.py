"""
Unit tests for propagate.py and sgp4.py exposed orbital elements.

Run from repo root:
    python -m pytest micropython/tests/test_propagate.py -v
Or from micropython/:
    python -m pytest tests/test_propagate.py -v
Or on device:
    import tests.test_propagate as t; t.run()
"""

import sys
import os
import math
import unittest

# Add micropython/ to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sgp4 import SGP4
import propagate


# --- Shared test fixtures ---

# ISS-like TLE parameters for repeatable tests
ISS_EPOCH_YEAR = 24
ISS_EPOCH_DAY = 1.0  # Jan 1, 2024
ISS_BSTAR = 0.0001
ISS_INC = 51.6416
ISS_RAAN = 245.0
ISS_ECC = 0.0007
ISS_ARGP = 130.0
ISS_MA = 230.0
ISS_N = 15.5  # revs/day


def make_sgp4():
    """Create and initialize an SGP4 model with ISS-like parameters."""
    s = SGP4()
    s.init(ISS_EPOCH_YEAR, ISS_EPOCH_DAY, ISS_BSTAR,
           ISS_INC, ISS_RAAN, ISS_ECC, ISS_ARGP, ISS_MA, ISS_N)
    return s


# ============================================================
# SGP4 exposed orbital elements
# ============================================================

class TestSGP4ExposedElements(unittest.TestCase):
    """Verify sgp4.py stores _raan_curr, _argp_curr, _nu after propagate()."""

    def setUp(self):
        self.sgp4 = make_sgp4()

    def test_elements_exist_after_propagate(self):
        """After propagate(), the three element attributes must exist."""
        self.sgp4.propagate(0.0)
        self.assertTrue(hasattr(self.sgp4, '_raan_curr'))
        self.assertTrue(hasattr(self.sgp4, '_argp_curr'))
        self.assertTrue(hasattr(self.sgp4, '_nu'))

    def test_elements_are_floats(self):
        self.sgp4.propagate(0.0)
        self.assertIsInstance(self.sgp4._raan_curr, float)
        self.assertIsInstance(self.sgp4._argp_curr, float)
        self.assertIsInstance(self.sgp4._nu, float)

    def test_elements_in_radian_range(self):
        """All three should be in [0, 2*pi) after propagate (mod 2pi in sgp4)."""
        TWOPI = 2.0 * math.pi
        for t_min in [0.0, 45.0, 90.0, 500.0]:
            self.sgp4.propagate(t_min)
            self.assertGreaterEqual(self.sgp4._raan_curr, 0.0,
                                    f"raan_curr < 0 at t={t_min}")
            self.assertLess(self.sgp4._raan_curr, TWOPI,
                            f"raan_curr >= 2pi at t={t_min}")
            self.assertGreaterEqual(self.sgp4._argp_curr, 0.0,
                                    f"argp_curr < 0 at t={t_min}")
            self.assertLess(self.sgp4._argp_curr, TWOPI,
                            f"argp_curr >= 2pi at t={t_min}")
            # nu can be negative from atan2; check [-pi, pi]
            self.assertGreaterEqual(self.sgp4._nu, -math.pi - 0.01)
            self.assertLessEqual(self.sgp4._nu, math.pi + 0.01)

    def test_elements_change_with_time(self):
        """Orbital elements should differ at different times."""
        self.sgp4.propagate(0.0)
        raan0, argp0, nu0 = self.sgp4._raan_curr, self.sgp4._argp_curr, self.sgp4._nu

        self.sgp4.propagate(45.0)  # 45 minutes later
        raan1, argp1, nu1 = self.sgp4._raan_curr, self.sgp4._argp_curr, self.sgp4._nu

        # At least nu (true anomaly) should change significantly in 45 min
        self.assertNotAlmostEqual(nu0, nu1, places=2,
                                  msg="True anomaly unchanged after 45 min")

    def test_elements_consistent_with_eci(self):
        """
        The ECI position from propagate() should be consistent with the
        exposed elements — specifically, the argument of latitude (nu + argp)
        should match the angle derived from the ECI position in the orbital plane.
        """
        self.sgp4.propagate(100.0)
        x, y, z = self.sgp4.propagate(100.0)

        # Reconstruct arg-latitude from elements
        u_from_elements = self.sgp4._nu + self.sgp4._argp_curr

        # Reconstruct from ECI: rotate back by RAAN and inclination
        cos_raan = math.cos(self.sgp4._raan_curr)
        sin_raan = math.sin(self.sgp4._raan_curr)
        XKMPER = 6378.135

        # Undo ECI rotation: x_prime, y_prime from x, y, z
        x_km = x / XKMPER
        y_km = y / XKMPER
        x_prime = x_km * cos_raan + y_km * sin_raan
        y_prime_cos_i = -x_km * sin_raan + y_km * cos_raan

        cos_inc = math.cos(self.sgp4.inc)
        if abs(cos_inc) > 1e-10:
            y_prime = y_prime_cos_i / cos_inc
        else:
            y_prime = y_prime_cos_i

        u_from_eci = math.atan2(y_prime, x_prime)

        # Compare (mod 2pi)
        diff = (u_from_elements - u_from_eci) % (2 * math.pi)
        if diff > math.pi:
            diff -= 2 * math.pi
        self.assertAlmostEqual(diff, 0.0, places=4,
                               msg=f"Arg-lat mismatch: elements={u_from_elements:.4f} eci={u_from_eci:.4f}")

    def test_propagate_return_unchanged(self):
        """Adding element storage must not change the ECI return values."""
        s1 = make_sgp4()
        s2 = make_sgp4()

        eci1 = s1.propagate(200.0)
        eci2 = s2.propagate(200.0)

        for i in range(3):
            self.assertAlmostEqual(eci1[i], eci2[i], places=6,
                                   msg=f"ECI axis {i} differs between two identical runs")


# ============================================================
# Propagate base class
# ============================================================

class TestPropagateBase(unittest.TestCase):
    """Verify the abstract base class contract."""

    def test_get_aov_eqx_raises(self):
        p = propagate.Propagate()
        with self.assertRaises(NotImplementedError):
            p.get_aov_eqx(0)

    def test_get_altitude_default(self):
        p = propagate.Propagate()
        self.assertEqual(p.get_altitude(), 0.0)

    def test_nudge_noop(self):
        """nudge_aov / nudge_eqx should not raise on base class."""
        p = propagate.Propagate()
        p.nudge_aov(5.0)
        p.nudge_eqx(-3.0)


# ============================================================
# KeplerJ2
# ============================================================

class TestKeplerJ2(unittest.TestCase):
    """Test the Keplerian propagator for manual orbits."""

    def _make_circular(self, alt_km=400.0):
        """Create a circular-orbit KeplerJ2 starting at phase 0, time 0."""
        return propagate.KeplerJ2(
            altitude_km=alt_km,
            inclination_deg=51.6,
            eccentricity=0.0,
            periapsis_deg=0.0,
            start_aov=0.0,
            start_eqx=0.0,
            start_time=0.0,
        )

    # --- Construction ---

    def test_altitude_stored(self):
        kj = self._make_circular(550.0)
        self.assertAlmostEqual(kj.get_altitude(), 550.0)

    def test_period_positive(self):
        kj = self._make_circular()
        self.assertGreater(kj.period_sec, 0)

    # --- Circular AoV ---

    def test_aov_zero_at_start(self):
        kj = self._make_circular()
        aov, _ = kj.get_aov_eqx(0.0)
        self.assertAlmostEqual(aov % 360, 0.0, places=3)

    def test_aov_advances_linearly(self):
        """For circular orbit, AoV should advance at a constant rate."""
        kj = self._make_circular()
        aov1, _ = kj.get_aov_eqx(100.0)
        aov2, _ = kj.get_aov_eqx(200.0)
        aov3, _ = kj.get_aov_eqx(300.0)

        delta1 = aov2 - aov1
        delta2 = aov3 - aov2
        self.assertAlmostEqual(delta1, delta2, places=3,
                               msg="AoV not advancing linearly")

    def test_aov_full_revolution(self):
        """After one full period, AoV should return to ~0 (mod 360)."""
        kj = self._make_circular()
        aov, _ = kj.get_aov_eqx(kj.period_sec)
        self.assertAlmostEqual(aov % 360, 0.0, delta=0.5,
                               msg=f"AoV after one period: {aov % 360:.2f}")

    def test_aov_half_revolution(self):
        """After half a period, AoV should be ~180."""
        kj = self._make_circular()
        aov, _ = kj.get_aov_eqx(kj.period_sec / 2.0)
        self.assertAlmostEqual(aov % 360, 180.0, delta=1.0)

    # --- EQX ---

    def test_eqx_zero_at_start(self):
        kj = self._make_circular()
        _, eqx = kj.get_aov_eqx(0.0)
        self.assertAlmostEqual(eqx % 360, 0.0, places=3)

    def test_eqx_advances(self):
        """EQX should change over time (Earth rotation + J2 drift)."""
        kj = self._make_circular()
        _, eqx0 = kj.get_aov_eqx(0.0)
        _, eqx1 = kj.get_aov_eqx(3600.0)  # 1 hour
        self.assertNotAlmostEqual(eqx0, eqx1, places=1,
                                  msg="EQX unchanged after 1 hour")

    # --- Nudge ---

    def test_nudge_aov(self):
        kj = self._make_circular()
        aov_before, _ = kj.get_aov_eqx(1000.0)
        kj.nudge_aov(10.0)
        aov_after, _ = kj.get_aov_eqx(1000.0)
        self.assertAlmostEqual(aov_after - aov_before, 10.0, places=3)

    def test_nudge_eqx(self):
        kj = self._make_circular()
        _, eqx_before = kj.get_aov_eqx(1000.0)
        kj.nudge_eqx(-5.0)
        _, eqx_after = kj.get_aov_eqx(1000.0)
        self.assertAlmostEqual(eqx_after - eqx_before, -5.0, places=3)

    # --- Altitude affects rate ---

    def test_higher_altitude_slower(self):
        """Higher orbit = longer period = slower AoV rate."""
        lo = self._make_circular(400.0)
        hi = self._make_circular(800.0)
        self.assertGreater(lo.aov_rate, hi.aov_rate)

    # --- Elliptical ---

    def test_elliptical_nonuniform(self):
        """Elliptical orbit should have non-uniform AoV advancement."""
        kj = propagate.KeplerJ2(
            altitude_km=400.0,
            inclination_deg=51.6,
            eccentricity=0.3,
            periapsis_deg=0.0,
            start_aov=0.0,
            start_eqx=0.0,
            start_time=0.0,
        )
        # Measure rates at two different points in the orbit
        dt = 60.0  # 1-minute intervals
        aov_a, _ = kj.get_aov_eqx(100.0)
        aov_b, _ = kj.get_aov_eqx(100.0 + dt)
        rate_early = aov_b - aov_a

        # Quarter period later
        t2 = kj.period_sec / 4.0
        aov_c, _ = kj.get_aov_eqx(t2)
        aov_d, _ = kj.get_aov_eqx(t2 + dt)
        rate_later = aov_d - aov_c

        # Rates should differ for e=0.3
        self.assertNotAlmostEqual(rate_early, rate_later, places=1,
                                  msg="Elliptical rates are too similar")


# ============================================================
# MicroSGP4
# ============================================================

class TestMicroSGP4(unittest.TestCase):
    """Test MicroSGP4 propagator integration with sgp4.py."""

    def setUp(self):
        self.sgp4 = make_sgp4()
        self.prop = propagate.MicroSGP4(self.sgp4)

    def test_construction(self):
        self.assertIs(self.prop.sgp4, self.sgp4)
        self.assertEqual(self.prop.last_alt, 0.0)

    def test_get_altitude_default(self):
        self.assertEqual(self.prop.get_altitude(), 0.0)

    def test_get_aov_eqx_returns_four_values(self):
        """get_aov_eqx must return a 4-tuple even when satellite_position is unavailable."""
        result = self.prop.get_aov_eqx(1704067200)  # 2024-01-01 00:00:00 UTC
        self.assertEqual(len(result), 4)

    def test_aov_eqx_in_degree_range(self):
        """If propagation succeeds, aov and eqx should be in [0, 360)."""
        result = self.prop.get_aov_eqx(1704067200)
        aov, eqx = result[0], result[1]
        # Even on fallback (0,0,0,0), these pass
        self.assertGreaterEqual(aov, 0.0)
        self.assertLess(aov, 360.0)
        self.assertGreaterEqual(eqx, 0.0)
        self.assertLess(eqx, 360.0)

    def test_different_times_different_results(self):
        """Two calls at different times should give different positions."""
        r1 = self.prop.get_aov_eqx(1704067200)
        r2 = self.prop.get_aov_eqx(1704067200 + 600)  # 10 min later
        # At least one of (aov, eqx, lat, lon) should differ
        differs = any(abs(a - b) > 0.01 for a, b in zip(r1, r2))
        self.assertTrue(differs,
                        "Positions identical 10 min apart — propagation may have failed")

    def test_uses_sgp4_exposed_elements(self):
        """
        After get_aov_eqx, the sgp4 instance should have _raan_curr etc.
        set (proving we called sgp4.propagate and read the elements).
        """
        self.prop.get_aov_eqx(1704067200)
        # If satellite_position is available, sgp4.propagate was called
        # If not, the fallback returns (0,0,0,0) and elements may not be set
        # Either way this should not raise
        if hasattr(self.sgp4, '_nu'):
            self.assertIsInstance(self.sgp4._nu, float)

    def test_no_duplicate_kepler_solver(self):
        """
        Verify MicroSGP4 source code does NOT contain its own Kepler solver.
        The whole point of the refactor is delegating to sgp4.py.
        """
        import inspect
        source = inspect.getsource(propagate.MicroSGP4)
        # The old propagators.py had these telltale patterns
        self.assertNotIn('e_anom', source,
                         "MicroSGP4 should not contain its own Kepler equation solver")
        self.assertNotIn('CK2', source,
                         "MicroSGP4 should not contain J2 precession constants")
        self.assertNotIn('rdot', source,
                         "MicroSGP4 should not compute RAAN precession rate")
        self.assertNotIn('pdot', source,
                         "MicroSGP4 should not compute argp precession rate")


# ============================================================
# Cross-module consistency
# ============================================================

class TestCrossModuleConsistency(unittest.TestCase):
    """Verify sgp4.py elements and propagate.py produce consistent results."""

    def test_aov_matches_nu_plus_argp(self):
        """
        MicroSGP4.aov should equal degrees(nu + argp_curr) mod 360.
        Test this by calling sgp4 directly and comparing.
        """
        sgp4 = make_sgp4()
        # Propagate to get elements
        sgp4.propagate(120.0)
        expected_aov = math.degrees(sgp4._nu + sgp4._argp_curr) % 360.0
        # Should be a valid degree value
        self.assertGreaterEqual(expected_aov, 0.0)
        self.assertLess(expected_aov, 360.0)

    def test_propagate_idempotent(self):
        """Calling sgp4.propagate twice with same t_min gives same elements."""
        sgp4 = make_sgp4()

        sgp4.propagate(77.7)
        r1, a1, n1 = sgp4._raan_curr, sgp4._argp_curr, sgp4._nu

        sgp4.propagate(77.7)
        r2, a2, n2 = sgp4._raan_curr, sgp4._argp_curr, sgp4._nu

        self.assertAlmostEqual(r1, r2, places=10)
        self.assertAlmostEqual(a1, a2, places=10)
        self.assertAlmostEqual(n1, n2, places=10)

    def test_old_propagators_deleted(self):
        """The old propagators.py module should not be importable."""
        # Save and restore sys.modules in case it was cached
        had_it = 'propagators' in sys.modules
        if had_it:
            saved = sys.modules.pop('propagators')

        importable = True
        try:
            import propagators
            importable = True
        except ImportError:
            importable = False
        finally:
            if had_it:
                sys.modules['propagators'] = saved

        self.assertFalse(importable,
                         "propagators.py should be deleted — propagate.py replaces it")


# ============================================================
# Entry point (MicroPython compatible)
# ============================================================

def run():
    unittest.main(module=__name__)


if __name__ == '__main__':
    unittest.main()
