#!/usr/bin/env python3
"""
CPU reference renderer for the Schwarzschild null-geodesic ray tracer.

This script reimplements, in NumPy, exactly the algorithm that index.html runs
on the GPU: the same RK4 integrator, the same orbit equation, the same
frequency-shift formula, the same thin-disk profile, and the same tone curve.
It exists for two reasons.

1. The images shipped in docs/media are produced by this script, so every
   picture in the README is reproducible from source on any machine, with no
   GPU and no browser involved.
2. Any change to the shader can be checked against this implementation. If the
   two diverge, one of them is wrong.

Geometric units are used throughout: G = c = M = 1. The event horizon sits at
r = 2, the photon sphere at r = 3, the innermost stable circular orbit at
r = 6, and the shadow edge at the critical impact parameter b = 3*sqrt(3).

Usage:
    python tools/render_reference.py --scene edge --width 1200 --ss 2
    python tools/render_reference.py --list
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

FLOAT = np.float32


# ----------------------------------------------------------------------------
# Scene description
# ----------------------------------------------------------------------------

@dataclass
class Scene:
    """A camera placement plus the disk and rendering settings that go with it."""

    name: str
    inclination_deg: float = 80.0     # 0 looks down the disk axis, 90 is edge-on
    azimuth_deg: float = 0.0
    radius: float = 60.0              # Schwarzschild radial coordinate of the observer
    fov_deg: float = 30.0
    disk_inner: float = 6.0
    disk_outer: float = 20.0
    peak_temperature: float = 4800.0  # kelvin, a display choice, see docs/PHYSICS.md
    turbulence: float = 0.50
    disk_brightness: float = 1.0
    show_disk: bool = True
    gravitational_redshift: bool = True
    doppler: bool = True
    lensing: float = 1.0              # scales the 3*M*u^2 term, 1.0 is physical
    stars: bool = True
    star_brightness: float = 1.0
    exposure: float = 0.90
    bloom: float = 0.55
    bloom_radius_px: float = 24.0
    bloom_threshold: float = 0.55
    steps: int = 1100
    dphi: float = 0.018
    escape_radius: float = 140.0
    seed: int = 7
    aspect: float = 16.0 / 9.0
    extra: dict = field(default_factory=dict)


SCENES = {
    # The hero frame: the same defaults the browser simulation opens with.
    "edge": Scene(name="edge"),
    "face": Scene(name="face", inclination_deg=10.0, exposure=1.10),
    "ring": Scene(name="ring", inclination_deg=87.0, radius=17.0, fov_deg=62.0,
                  disk_outer=16.0, exposure=0.42, bloom=0.70),
    # Comparison frames. Each one differs from "edge" by a single switch.
    "flat": Scene(name="flat", lensing=0.0),
    "nodoppler": Scene(name="nodoppler", doppler=False),
    "noredshift": Scene(name="noredshift", gravitational_redshift=False),
    "nodisk": Scene(name="nodisk", show_disk=False, star_brightness=2.2,
                    exposure=1.6, fov_deg=26.0),
}


# ----------------------------------------------------------------------------
# Colour
# ----------------------------------------------------------------------------

_XYZ_TO_SRGB = np.array([
    [3.2404542, -1.5371385, -0.4985314],
    [-0.9692660, 1.8760108, 0.0415560],
    [0.0556434, -0.2040259, 1.0572252],
], dtype=np.float64)


def blackbody_rgb(temperature):
    """Linear sRGB chromaticity of a blackbody, normalised to unit luminance.

    The Planckian locus is evaluated with the cubic approximation of the CIE
    1931 chromaticity coordinates that is commonly attributed to Kim et al.
    (2002). That bibliographic attribution is unverified; the fit itself is
    accurate over 1700 K to 25000 K, which is the range clamped here.
    """
    t = np.clip(np.asarray(temperature, dtype=np.float64), 1700.0, 25000.0)
    t2, t3 = t * t, t * t * t

    x = np.where(
        t < 4000.0,
        -0.2661239e9 / t3 - 0.2343589e6 / t2 + 0.8776956e3 / t + 0.179910,
        -3.0258469e9 / t3 + 2.1070379e6 / t2 + 0.2226347e3 / t + 0.240390,
    )
    x2, x3 = x * x, x * x * x

    y = np.where(
        t < 2222.0,
        -1.1063814 * x3 - 1.34811020 * x2 + 2.18555832 * x - 0.20219683,
        np.where(
            t < 4000.0,
            -0.9549476 * x3 - 1.37418593 * x2 + 2.09137015 * x - 0.16748867,
            3.0817580 * x3 - 5.87338670 * x2 + 3.75112997 * x - 0.37001483,
        ),
    )
    y = np.maximum(y, 1e-4)

    xyz = np.stack([x / y, np.ones_like(y), (1.0 - x - y) / y], axis=-1)
    rgb = xyz @ _XYZ_TO_SRGB.T
    return np.maximum(rgb, 0.0).astype(FLOAT)


# ----------------------------------------------------------------------------
# Hashes and value noise, ported from the shader
# ----------------------------------------------------------------------------

def _fract(a):
    return a - np.floor(a)


def hash12(px, py):
    p3x = _fract(px * 0.1031)
    p3y = _fract(py * 0.1031)
    p3z = _fract(px * 0.1031)
    d = p3x * (p3y + 33.33) + p3y * (p3z + 33.33) + p3z * (p3x + 33.33)
    p3x, p3y, p3z = p3x + d, p3y + d, p3z + d
    return _fract((p3x + p3y) * p3z)


def hash33(px, py, pz):
    p3x = _fract(px * 0.1031)
    p3y = _fract(py * 0.1030)
    p3z = _fract(pz * 0.0973)
    d = p3x * (p3y + 33.33) + p3y * (p3x + 33.33) + p3z * (p3z + 33.33)
    p3x, p3y, p3z = p3x + d, p3y + d, p3z + d
    return (_fract((p3x + p3y) * p3z),
            _fract((p3x + p3x) * p3y),
            _fract((p3y + p3x) * p3x))


def vnoise(px, py, period_x):
    ix, iy = np.floor(px), np.floor(py)
    fx, fy = px - ix, py - iy
    fx = fx * fx * (3.0 - 2.0 * fx)
    fy = fy * fy * (3.0 - 2.0 * fy)
    i0 = np.mod(ix, period_x)
    i1 = np.mod(ix + 1.0, period_x)
    a = hash12(i0, iy)
    b = hash12(i1, iy)
    c = hash12(i0, iy + 1.0)
    d = hash12(i1, iy + 1.0)
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy


def fbm(px, py, period_x, octaves=4):
    total = np.zeros_like(px)
    amp, per = 0.5, float(period_x)
    x, y = px.copy(), py.copy()
    for _ in range(octaves):
        total += amp * vnoise(x, y, per)
        x, y = x * 2.0, y * 2.0
        per *= 2.0
        amp *= 0.5
    return total


# ----------------------------------------------------------------------------
# Sky
# ----------------------------------------------------------------------------

def sky_color(direction, scene: Scene):
    """Procedural star field plus a faint diffuse band. Invented, not a catalogue."""
    if not scene.stars:
        return np.zeros(direction.shape[:-1] + (3,), dtype=FLOAT)

    dx, dy, dz = direction[..., 0], direction[..., 1], direction[..., 2]
    ax, ay, az = np.abs(dx), np.abs(dy), np.abs(dz)

    face = np.zeros_like(dx)
    u = np.zeros_like(dx)
    v = np.zeros_like(dx)

    mx = (ax >= ay) & (ax >= az)
    my = (~mx) & (ay >= az)
    mz = (~mx) & (~my)

    u[mx], v[mx] = dy[mx] / ax[mx], dz[mx] / ax[mx]
    face[mx] = np.where(dx[mx] > 0, 0.0, 1.0)
    u[my], v[my] = dx[my] / ay[my], dz[my] / ay[my]
    face[my] = np.where(dy[my] > 0, 2.0, 3.0)
    u[mz], v[mz] = dx[mz] / az[mz], dy[mz] / az[mz]
    face[mz] = np.where(dz[mz] > 0, 4.0, 5.0)

    cells = 62.0
    gx, gy = u * cells, v * cells
    gix, giy = np.floor(gx), np.floor(gy)
    fx, fy = gx - gix, gy - giy

    out = np.zeros(dx.shape + (3,), dtype=FLOAT)
    for oj in (-1.0, 0.0, 1.0):
        for oi in (-1.0, 0.0, 1.0):
            hx, hy, hz = hash33(gix + oi, giy + oj, face)
            keep = hz <= 0.42
            ddx = fx - oi - hx
            ddy = fy - oj - hy
            d2 = ddx * ddx + ddy * ddy
            mag = _fract(hz * 71.17) ** 5 + 0.012
            temp = 2900.0 + (13000.0 - 2900.0) * _fract(hx * 37.91) ** 1.6
            weight = (mag * np.exp(-d2 * 210.0) * keep).astype(FLOAT)
            out += blackbody_rgb(temp) * weight[..., None]

    band_normal = np.array([0.34, -0.52, 0.78], dtype=FLOAT)
    band_normal /= np.linalg.norm(band_normal)
    s = dx * band_normal[0] + dy * band_normal[1] + dz * band_normal[2]
    band = np.exp(-s * s * 13.0)
    clumps = fbm(np.arctan2(dy, dx) * 2.2, dz * 3.4, 16.0)
    out += (np.array([0.030, 0.034, 0.052], dtype=FLOAT)
            * (band * (0.35 + 0.9 * clumps))[..., None])

    return out * scene.star_brightness


# ----------------------------------------------------------------------------
# Disk emission
# ----------------------------------------------------------------------------

def disk_emission(r, psi, lam, scene: Scene, time_s=0.0):
    """Observed colour and brightness of a thin Keplerian disk element.

    The frequency shift for a circular equatorial orbit in Schwarzschild is
        g = sqrt(1 - 3M/r) / (1 - Omega * lambda),   Omega = sqrt(M/r^3)
    where lambda = L_z / E is the conserved axial impact parameter of the photon.
    Observed specific intensity follows I_obs = g^4 * I_emit, which is
    Liouville's theorem applied to the invariant I_nu / nu^3.
    """
    r_in = scene.disk_inner
    x_in = np.sqrt(r_in / r)
    profile = np.maximum((r_in ** 3) / (r ** 3) * (1.0 - x_in), 1e-8)
    # 0.487872 is the maximum of profile**0.25, attained at r = (49/36) r_in
    t_emit = scene.peak_temperature * profile ** 0.25 / 0.487872

    omega = 1.0 / (r * np.sqrt(r))
    g_grav = np.sqrt(np.maximum(1.0 - 2.0 / r, 1e-5))
    g_full = (np.sqrt(np.maximum(1.0 - 3.0 / r, 1e-5))
              / np.maximum(1.0 - omega * lam, 0.02))

    g = np.ones_like(r)
    if scene.gravitational_redshift:
        g = g * g_grav
    if scene.doppler:
        g = g * (g_full / g_grav)

    t_obs = np.clip(t_emit * g, 800.0, 40000.0)
    rgb = blackbody_rgb(t_obs)
    intensity = (t_obs / scene.peak_temperature) ** 4

    if scene.turbulence > 0.001:
        shear = psi - omega * time_s
        n = fbm(shear * (14.0 / (2.0 * np.pi)), np.log(r) * 5.2, 14.0)
        intensity = intensity * (1.0 - scene.turbulence
                                 + scene.turbulence * (0.35 + 1.55 * n))

    edge_in = np.clip((r - r_in) / r_in / 0.12, 0.0, 1.0)
    edge_in = edge_in * edge_in * (3.0 - 2.0 * edge_in)
    t_out = np.clip((r / scene.disk_outer - 0.86) / 0.14, 0.0, 1.0)
    edge_out = 1.0 - t_out * t_out * (3.0 - 2.0 * t_out)
    intensity = intensity * edge_in * edge_out * scene.disk_brightness

    return (rgb * intensity[..., None]).astype(FLOAT)


# ----------------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------------

def camera_basis(scene: Scene):
    i = np.radians(scene.inclination_deg)
    a = np.radians(scene.azimuth_deg)
    pos = np.array([
        scene.radius * np.sin(i) * np.cos(a),
        scene.radius * np.sin(i) * np.sin(a),
        scene.radius * np.cos(i),
    ], dtype=np.float64)
    fwd = -pos / np.linalg.norm(pos)
    up_world = np.array([0.0, 0.0, 1.0]) if abs(fwd[2]) < 0.9995 else np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up_world)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return pos, fwd, right, up


# ----------------------------------------------------------------------------
# The integrator
# ----------------------------------------------------------------------------

def trace(scene: Scene, width: int, height: int, verbose=True,
          row_start=0, row_stop=None):
    """Integrate one null geodesic per pixel and return a linear HDR image.

    Rows [row_start, row_stop) of a width x height frame are rendered. Working
    on a band at a time keeps peak memory proportional to the band, which
    matters because every ray in flight carries about a dozen float64 arrays.
    """
    row_stop = height if row_stop is None else row_stop
    pos, fwd, right, up = camera_basis(scene)
    tan_half = np.tan(np.radians(scene.fov_deg) * 0.5)
    aspect = width / height

    rows = np.arange(row_start, row_stop)
    px = (np.arange(width, dtype=np.float64) + 0.5) / width * 2.0 - 1.0
    py = 1.0 - (rows.astype(np.float64) + 0.5) / height * 2.0
    gx, gy = np.meshgrid(px, py)
    height_band = rows.size

    d = (fwd[None, None, :]
         + tan_half * (gx[..., None] * aspect * right[None, None, :]
                       + gy[..., None] * up[None, None, :]))
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    d = d.reshape(-1, 3)

    n_rays = d.shape[0]
    o = pos
    r0 = float(np.linalg.norm(o))
    e1 = (o / r0).astype(np.float64)

    nv = np.cross(np.broadcast_to(o, d.shape), d)
    nl = np.linalg.norm(nv, axis=-1, keepdims=True)
    fallback = np.cross(e1, np.array([0.0173, 0.9986, 0.0491]))
    fallback /= np.linalg.norm(fallback)
    nh = np.where(nl > 1e-9, nv / np.maximum(nl, 1e-30), fallback[None, :])
    e2 = np.cross(nh, np.broadcast_to(e1, d.shape))
    e2 /= np.linalg.norm(e2, axis=-1, keepdims=True)

    d_rad = np.einsum("ij,j->i", d, e1)
    d_tan = np.maximum(np.einsum("ij,ij->i", d, e2), 1e-6)

    f0 = 1.0 - 2.0 / r0
    sf0 = np.sqrt(f0)

    u = np.full(n_rays, 1.0 / r0)
    w = -sf0 * d_rad / (r0 * d_tan)
    b = r0 * d_tan / sf0
    lam = -b * nh[:, 2]

    phi = np.zeros(n_rays)
    s_prev = np.full(n_rays, e1[2])

    color = np.zeros((n_rays, 3), dtype=FLOAT)
    idx = np.arange(n_rays)              # indices of the rays still in flight

    e1z, e2z = e1[2], e2[:, 2].copy()
    gr = scene.lensing
    h = scene.dphi
    u_escape = 1.0 / scene.escape_radius

    t_start = time.time()
    for step in range(scene.steps):
        if idx.size == 0:
            break

        u_prev, w_prev, phi_prev = u.copy(), w.copy(), phi.copy()

        k1u, k1w = w, 3.0 * gr * u * u - u
        u2, w2 = u + 0.5 * h * k1u, w + 0.5 * h * k1w
        k2u, k2w = w2, 3.0 * gr * u2 * u2 - u2
        u3, w3 = u + 0.5 * h * k2u, w + 0.5 * h * k2w
        k3u, k3w = w3, 3.0 * gr * u3 * u3 - u3
        u4, w4 = u + h * k3u, w + h * k3w
        k4u, k4w = w4, 3.0 * gr * u4 * u4 - u4

        u = u + (h / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
        w = w + (h / 6.0) * (k1w + 2.0 * k2w + 2.0 * k3w + k4w)
        phi = phi + h

        done = np.zeros(idx.size, dtype=bool)

        # escaped inside a single step
        gone = u <= 1e-7
        if gone.any():
            cp, sp = np.cos(phi_prev[gone]), np.sin(phi_prev[gone])
            rh = cp[:, None] * e1[None, :] + sp[:, None] * e2[gone]
            ph = -sp[:, None] * e1[None, :] + cp[:, None] * e2[gone]
            vd = -w_prev[gone][:, None] * rh + u_prev[gone][:, None] * ph
            vd /= np.linalg.norm(vd, axis=-1, keepdims=True)
            color[idx[gone]] = sky_color(vd.astype(FLOAT), scene)
            done |= gone

        # crossed the horizon, stays black
        captured = (~done) & (u > 0.5)
        done |= captured

        s_cur = np.cos(phi) * e1z + np.sin(phi) * e2z

        if scene.show_disk:
            cross = (~done) & (s_prev * s_cur < 0.0)
            if cross.any():
                t = s_prev[cross] / (s_prev[cross] - s_cur[cross])
                uc = u_prev[cross] + (u[cross] - u_prev[cross]) * t
                rc = 1.0 / np.maximum(uc, 1e-6)
                hit_local = (rc >= scene.disk_inner) & (rc <= scene.disk_outer)
                if hit_local.any():
                    where = np.flatnonzero(cross)[hit_local]
                    phic = phi_prev[where] + t[hit_local] * h
                    cp, sp = np.cos(phic), np.sin(phic)
                    pc = (rc[hit_local][:, None]
                          * (cp[:, None] * e1[None, :] + sp[:, None] * e2[where]))
                    psi = np.arctan2(pc[:, 1], pc[:, 0])
                    color[idx[where]] = disk_emission(
                        rc[hit_local], psi, lam[where], scene)
                    done[where] = True

        s_prev = s_cur

        # escaped: far away and still receding
        out = (~done) & (u < u_escape) & (w < 0.0)
        if out.any():
            cp, sp = np.cos(phi[out]), np.sin(phi[out])
            rh = cp[:, None] * e1[None, :] + sp[:, None] * e2[out]
            ph = -sp[:, None] * e1[None, :] + cp[:, None] * e2[out]
            vd = -w[out][:, None] * rh + u[out][:, None] * ph
            vd /= np.linalg.norm(vd, axis=-1, keepdims=True)
            color[idx[out]] = sky_color(vd.astype(FLOAT), scene)
            done |= out

        if done.any():
            keep = ~done
            idx = idx[keep]
            u, w, phi = u[keep], w[keep], phi[keep]
            s_prev = s_prev[keep]
            e2, e2z, lam = e2[keep], e2z[keep], lam[keep]
            u_prev = w_prev = phi_prev = None

        if verbose and step % 100 == 0:
            print(f"  step {step:4d}  active {idx.size:9d}  "
                  f"{time.time() - t_start:6.1f} s", flush=True)

    return color.reshape(height_band, width, 3)


# ----------------------------------------------------------------------------
# Post processing
# ----------------------------------------------------------------------------

def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0)


def post_process(hdr, scene: Scene, supersample: int):
    from scipy.ndimage import gaussian_filter, zoom

    image = hdr.astype(np.float32)
    if scene.bloom > 0.001:
        bright = np.maximum(image - scene.bloom_threshold, 0.0)
        # bloom_radius_px is defined against a 1600 pixel wide reference frame,
        # so that the halo keeps the same angular size at any output resolution
        sigma = scene.bloom_radius_px * (image.shape[1] / 1600.0) * 0.45
        halo = np.stack([gaussian_filter(bright[..., c], sigma) for c in range(3)], axis=-1)
        image = image + halo * scene.bloom

    image = image * scene.exposure
    image = aces(image)
    image = np.power(image, 1.0 / 2.2)

    if supersample > 1:
        k = supersample
        h, w, _ = image.shape
        image = image[: h // k * k, : w // k * k]
        image = image.reshape(h // k, k, w // k, k, 3).mean(axis=(1, 3))

    return (np.clip(image, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scene", default="edge", help="scene name, see --list")
    parser.add_argument("--width", type=int, default=1200, help="output width in pixels")
    parser.add_argument("--ss", type=int, default=2, help="supersampling factor per axis")
    parser.add_argument("--steps", type=int, default=None, help="override integration steps")
    parser.add_argument("--out", default=None, help="output PNG path")
    parser.add_argument("--tile-rows", type=int, default=180,
                        help="rows rendered per band, lower it to cut peak memory")
    parser.add_argument("--list", action="store_true", help="list the available scenes")
    args = parser.parse_args()

    if args.list:
        for key, scene in SCENES.items():
            print(f"{key:12s} i={scene.inclination_deg:5.1f} deg  "
                  f"r={scene.radius:5.1f} M  fov={scene.fov_deg:4.1f} deg  "
                  f"lensing={scene.lensing}")
        return

    scene = SCENES[args.scene]
    if args.steps is not None:
        scene.steps = args.steps

    width = args.width * args.ss
    height = int(round(width / scene.aspect))

    print(f"scene {scene.name}: {width}x{height} rays, "
          f"{scene.steps} steps, dphi {scene.dphi}")
    t0 = time.time()
    band = max(1, int(args.tile_rows))
    tiles = []
    for row in range(0, height, band):
        stop = min(row + band, height)
        tiles.append(trace(scene, width, height, verbose=False,
                           row_start=row, row_stop=stop))
        print(f"  rows {row:5d} to {stop:5d}   {time.time() - t0:7.1f} s", flush=True)
    hdr = np.concatenate(tiles, axis=0)
    del tiles
    print(f"integration finished in {time.time() - t0:.1f} s")

    rgb = post_process(hdr, scene, args.ss)
    out = args.out or f"docs/media/{scene.name}.png"
    Image.fromarray(rgb).save(out, optimize=True)
    print(f"wrote {out}  ({rgb.shape[1]}x{rgb.shape[0]})")


if __name__ == "__main__":
    main()
