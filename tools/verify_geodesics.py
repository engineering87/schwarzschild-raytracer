#!/usr/bin/env python3
"""
Numerical verification of the null-geodesic integrator.

The renderer stands or falls on one claim: that the RK4 integration of

    d2u/dphi2 + u = 3 (GM/c2) u2,        u = 1/r

really is the Schwarzschild null geodesic and not an approximation dressed up
as one. This script checks that claim against two quantities with exact closed
forms, using the same arithmetic the shader uses.

Test 1, photon capture cross-section.
    Bisection on the impact parameter of a ray coming in from a very large
    radius separates captured trajectories from escaping ones. The boundary
    must be the critical impact parameter b_crit = 3 sqrt(3) M = 5.196152 M,
    which is the impact parameter of the unstable circular photon orbit at
    r = 3M. This single number sets the angular size of the shadow, so any
    error here is visible in every frame.

Test 2, light deflection.
    The total bending of a ray that passes at impact parameter b has the
    well known expansion

        alpha = 4M/b + (15 pi / 4) (M/b)^2 + (128/3) (M/b)^3 + ...

    The leading term is the 1915 Einstein value. The integrator must reproduce
    the series, including the second order term, otherwise it is solving the
    Newtonian problem rather than the relativistic one. The trajectory is
    integrated between two points at the same radius on either side of
    periastron, and the small angle subtended between that radius and infinity
    is added back analytically.

Exit code is zero when every tolerance is met.

Units are geometric: G = c = M = 1.
"""

from __future__ import annotations

import math
import sys

B_CRIT = 3.0 * math.sqrt(3.0)


def integrate(r0: float, b: float, h: float, lensing: float = 1.0,
              max_steps: int = 100_000_000):
    """Integrate one inbound null geodesic launched at radius r0.

    Returns the azimuth swept when the ray comes back out to radius r0, or
    None when the ray crosses the horizon. The integrator, the state variables,
    and the step order are identical to the GLSL implementation in index.html.
    """
    f0 = 1.0 - 2.0 / r0
    sf0 = math.sqrt(f0)
    d_tan = b * sf0 / r0
    if d_tan > 1.0:
        return None                      # the ray never reaches this radius
    d_rad = -math.sqrt(1.0 - d_tan * d_tan)

    u = 1.0 / r0
    w = -sf0 * d_rad / (r0 * d_tan)      # du/dphi in the local static frame
    phi = 0.0
    u_end = 1.0 / r0

    for _ in range(max_steps):
        k1u, k1w = w, 3.0 * lensing * u * u - u
        u2, w2 = u + 0.5 * h * k1u, w + 0.5 * h * k1w
        k2u, k2w = w2, 3.0 * lensing * u2 * u2 - u2
        u3, w3 = u + 0.5 * h * k2u, w + 0.5 * h * k2w
        k3u, k3w = w3, 3.0 * lensing * u3 * u3 - u3
        u4, w4 = u + h * k3u, w + h * k3w
        k4u, k4w = w4, 3.0 * lensing * u4 * u4 - u4

        u_before = u
        u += (h / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
        w += (h / 6.0) * (k1w + 2.0 * k2w + 2.0 * k3w + k4w)
        phi += h

        if u > 0.5:                      # inside the horizon at r = 2M
            return None
        if w < 0.0 and u <= u_end:       # back out at the launch radius
            t = (u_before - u_end) / (u_before - u) if u_before != u else 0.0
            return phi - h * (1.0 - t)

    return None


def test_critical_impact_parameter(h=0.002, r0=1.0e6, iterations=60):
    lo, hi = 4.0, 7.0
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        if integrate(r0, mid, h) is None:
            lo = mid                     # captured, so b_crit is larger
        else:
            hi = mid
    return 0.5 * (lo + hi)


def deflection(b, h=0.002, r0=1.0e7):
    phi = integrate(r0, b, h)
    if phi is None:
        return None
    # The integration runs between two points at r0 rather than between the
    # asymptotes. Add back the angle b/r0 subtended on each side.
    return phi - math.pi + 2.0 * b / r0


def series(b, order):
    terms = [4.0 / b, 15.0 * math.pi / 4.0 / b ** 2, 128.0 / 3.0 / b ** 3]
    return sum(terms[:order])


def main():
    failures = 0
    print("Schwarzschild null-geodesic verification")
    print("units: G = c = M = 1\n")

    print("Test 1  critical impact parameter")
    measured = test_critical_impact_parameter()
    error = abs(measured - B_CRIT)
    print(f"  measured   b_crit = {measured:.9f} M")
    print(f"  analytic 3*sqrt(3) = {B_CRIT:.9f} M")
    print(f"  absolute error     = {error:.2e}")
    ok = error < 1e-6
    failures += 0 if ok else 1
    print(f"  {'PASS' if ok else 'FAIL'}  tolerance 1e-6\n")

    print("Test 2  light deflection against the post-Newtonian series")
    print(f"  {'b/M':>8} {'measured':>14} {'4M/b':>14} {'+2nd order':>14} "
          f"{'residual':>12} {'3rd term':>12}")
    for b in (30.0, 50.0, 100.0, 400.0):
        alpha = deflection(b)
        first = series(b, 1)
        second = series(b, 2)
        residual = alpha - second
        third = 128.0 / 3.0 / b ** 3
        print(f"  {b:8.0f} {alpha:14.9f} {first:14.9f} {second:14.9f} "
              f"{residual:12.3e} {third:12.3e}")
        # The residual after the second order term must be explained by the
        # third order term, within a factor of two.
        ok = abs(residual - third) < max(0.6 * third, 5e-8)
        failures += 0 if ok else 1
        if not ok:
            print(f"           FAIL  residual not explained by the 3rd order term")
    print(f"  {'PASS' if failures == 0 else 'FAIL'}\n")

    print("Test 3  step size independence")
    ref = deflection(50.0, h=0.004)
    fine = deflection(50.0, h=0.0005)
    drift = abs(ref - fine)
    print(f"  h = 0.0040 -> {ref:.9f}")
    print(f"  h = 0.0005 -> {fine:.9f}")
    print(f"  drift      =  {drift:.2e}")
    ok = drift < 1e-8
    failures += 0 if ok else 1
    print(f"  {'PASS' if ok else 'FAIL'}  tolerance 1e-8\n")

    print("all tests passed" if failures == 0 else f"{failures} check(s) failed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
