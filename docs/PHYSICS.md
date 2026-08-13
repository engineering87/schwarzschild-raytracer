# Physics notes

Everything below is written in geometric units, $G = c = M = 1$. Distances are
therefore measured in units of $GM/c^{2}$, which is 1.48 km for the Sun and about
$6.0 \times 10^{9}$ km for the M87 hole. The four radii that matter are the event
horizon at $r = 2$, the photon sphere at $r = 3$, the shadow edge at impact
parameter $b = 3\sqrt{3} \approx 5.196$, and the innermost stable circular orbit
at $r = 6$.

## 1. The metric

The exterior of a static, uncharged, non-rotating mass is the Schwarzschild
solution, published by Karl Schwarzschild in January 1916, weeks after the
field equations themselves:

$$ds^{2} = -\left(1 - \frac{2M}{r}\right)dt^{2} + \left(1 - \frac{2M}{r}\right)^{-1}dr^{2} + r^{2}\left(d\theta^{2} + \sin^{2}\theta \, d\varphi^{2}\right)$$

Birkhoff's theorem makes this the unique spherically symmetric vacuum solution,
so it is not a special case chosen for convenience. It is the only option once
spherical symmetry is assumed.

## 2. Reducing the ray to one equation

Spherical symmetry has a consequence that the whole renderer depends on. A null
geodesic starting at position $\mathbf{o}$ with spatial direction $\mathbf{d}$
stays forever in the plane spanned by $\mathbf{o}$ and $\mathbf{d}$. There is no way for it to leave that plane,
because there is no preferred direction to leave towards. The trajectory is
therefore a two dimensional problem, whatever the three dimensional geometry of
the scene looks like.

Inside that plane, with $u = 1/r$, the null geodesic satisfies

$$\frac{d^{2}u}{d\varphi^{2}} + u = 3Mu^{2}$$

The left hand side alone gives $u = \cos(\varphi - \varphi_{0})/b$, which is a straight line in
polar coordinates. The single term on the right is general relativity. It is
not a perturbation bolted onto flat optics: the equation is exact, and the
renderer integrates it as written with fixed step RK4.

The conserved quantities come out of the same setup. For a photon with energy
$E = -p_{t}$ and total angular momentum $L$, the impact parameter is $b = L/E$,
and the first integral of the orbit equation is

$$\left(\frac{du}{d\varphi}\right)^{2} + u^{2} - 2Mu^{3} = \frac{1}{b^{2}}$$

## 3. Initial conditions in the observer frame

The camera is a static observer at Schwarzschild radial coordinate $r_{0}$. Its
local orthonormal frame is the one an actual instrument at that radius would
use, and it differs from the coordinate basis by the redshift factor. Writing
$f_{0} = 1 - 2M/r_{0}$ and splitting the unit view direction into a radial part
$d_{r}$ and a tangential part $d_{t}$:

$$b = \frac{r_{0}\, d_{t}}{\sqrt{f_{0}}}
\qquad\qquad
\frac{du}{d\varphi} = -\frac{\sqrt{f_{0}}\; d_{r}}{r_{0}\, d_{t}}$$

The $\sqrt{f_{0}}$ factors are what make the field of view correct. Dropping them gives
a picture that is qualitatively similar and quantitatively wrong, and the error
grows as the camera approaches the hole.

The axial impact parameter follows from the plane normal
$\hat{n} = \widehat{\mathbf{o} \times \mathbf{d}}$. For the physical photon, which
travels towards the camera rather than away from it,

$$\lambda = \frac{L_{z}}{E} = -b \, \hat{n}_{z}$$

This is the quantity the disk needs, and it costs nothing extra: it is fixed by
the same initial conditions as the trajectory.

## 4. Termination

Each ray ends in one of three ways.

- $u > 1/2$, meaning $r < 2M$. The photon crossed the horizon. The pixel is
  black. Collectively these pixels are the shadow, and its boundary is the set
  of rays with $b = 3\sqrt{3}\,M$.
- The ray crosses the equatorial plane at a radius inside the disk annulus.
  The disk is optically thick, so the first such crossing terminates the ray.
  Crossings inside $r_{\mathrm{in}}$ or beyond $r_{\mathrm{out}}$ are ignored and the integration
  continues, which is what produces the secondary image of the disk seen
  underneath the hole.
- $u$ falls below $1/r_{\mathrm{escape}}$ while still decreasing. The photon
  escaped. Its asymptotic direction is approximated by the local velocity
  direction, $\widehat{-u'\,\hat{r} + u\,\hat{\varphi}}$, and used to sample the
  background.

## 5. Radiative transfer for the disk

The disk is geometrically thin, optically thick, confined to the equatorial
plane, and on circular Keplerian orbits with angular velocity
$\Omega = \sqrt{M/r^{3}}$. The four velocity of that flow is
$u^{\mu} \propto (1, 0, 0, \Omega)$ with $u^{t} = 1/\sqrt{1 - 3M/r}$, which
diverges at the photon sphere and is the reason no circular orbit exists inside
$r = 3M$.

The ratio of observed to emitted frequency is

$$g = \frac{\nu_{\mathrm{obs}}}{\nu_{\mathrm{em}}} = \frac{\sqrt{1 - 3M/r}}{1 - \Omega\lambda}$$

Both $\lambda$ and $r$ are already known at the crossing point, so this is a direct
evaluation rather than a fit. The expression splits cleanly into the two
effects the interface exposes as separate switches:

$$g_{\mathrm{grav}} = \sqrt{1 - \frac{2M}{r}}
\qquad\qquad
g_{\mathrm{Dopp}} = \frac{g}{g_{\mathrm{grav}}} = \frac{1}{\gamma\left(1 - \boldsymbol{\beta}\cdot\hat{n}\right)}$$

with $\beta = \sqrt{M/r}\,/\sqrt{1 - 2M/r}$ the orbital speed measured by a local
static observer. At the ISCO that speed is exactly $1/2$, and the largest
blueshift available anywhere on a Keplerian disk is $g = \sqrt{2} \approx 1.414$,
reached by a photon emitted tangentially at $r = 6M$ on the approaching side.

Specific intensity divided by the cube of frequency is a Lorentz invariant that
is constant along a ray, which is Liouville's theorem in the form usually
attributed to the 1934 argument. Integrating over frequency gives the
bolometric result used here:

$$I_{\mathrm{obs}} = g^{4} I_{\mathrm{em}}$$

The renderer exploits a convenient identity. Since the emitted intensity of a
blackbody scales as $T^{4}$ and the observed temperature is $gT$, the observed
intensity is simply $(gT)^{4}$. Colour and brightness therefore both follow from
the single observed temperature, with no separate bookkeeping.

## 6. The temperature profile

The radial run of temperature is the standard thin-disk result of Shakura and
Sunyaev (1973), with a torque-free inner boundary:

$$T(r) \propto \left[\frac{1}{r^{3}}\left(1 - \sqrt{\frac{r_{\mathrm{in}}}{r}}\right)\right]^{1/4}$$

The bracket vanishes at $r_{\mathrm{in}}$, rises to a maximum at
$r = \tfrac{49}{36}\,r_{\mathrm{in}}$, and falls as $r^{-3/4}$ far out. The absolute normalisation is a display parameter
and is discussed in the honesty section of the README. The shape is not.

## 7. Verification

`tools/verify_geodesics.py` checks the integrator against two closed forms.
Running it on the reference machine produces the following.

**Critical impact parameter.** Bisection on $b$ separates capture from escape.

| quantity | value |
| --- | --- |
| measured | 5.196152423 M |
| analytic $3\sqrt{3}$ | 5.196152423 M |
| absolute error | 1.8 × 10⁻¹³ |

**Light deflection.** The measured bending is compared with the expansion

$$\alpha = \frac{4M}{b} + \frac{15\pi}{4}\left(\frac{M}{b}\right)^{2} + \frac{128}{3}\left(\frac{M}{b}\right)^{3} + \cdots$$

| $b/M$ | measured $\alpha$ (rad) | 4M/b | through 2nd order | residual | 3rd order term |
| --- | --- | --- | --- | --- | --- |
| 30 | 0.148248087 | 0.133333333 | 0.146423303 | 1.83 × 10⁻³ | 1.58 × 10⁻³ |
| 50 | 0.085083450 | 0.080000000 | 0.084712389 | 3.71 × 10⁻⁴ | 3.41 × 10⁻⁴ |
| 100 | 0.041222540 | 0.040000000 | 0.041178097 | 4.44 × 10⁻⁵ | 4.27 × 10⁻⁵ |
| 400 | 0.010074304 | 0.010000000 | 0.010073631 | 6.73 × 10⁻⁷ | 6.67 × 10⁻⁷ |

The residual after the second order term tracks the third order term to about
one percent at large $b$, which is the expected behaviour of a correct
integration truncated at a known order. Halving the step from 0.004 to 0.0005
moves the answer by 8 × 10⁻¹⁰ radians, so the remaining error is series
truncation and not numerics.

**Beaming asymmetry.** `tools/measure_beaming.py` renders the default scene and
sums the linear luminance of the two halves of the frame. The approaching half
is 4.55 times brighter than the receding half. With the Doppler factor
disabled the same measurement returns 1.00, so the asymmetry is attributable to
that term alone and not to the geometry of the disk or to the framing.

## 8. Known limitations

These are the honest boundaries of the model. Each one is a deliberate choice
rather than an oversight.

**Spin is zero.** Schwarzschild has no frame dragging, no ergosphere, and no
prograde or retrograde asymmetry in the ISCO. Real holes almost certainly spin,
and the observational consequences are large: for a maximally rotating Kerr
hole the ISCO moves from $6M$ to $M$ for prograde orbits, which changes both
the peak temperature and the shape of the shadow.

**Colour is a mapping, not a measurement.** A disk around a stellar mass hole
peaks in soft X-rays near $10^{7}$ K. Around a supermassive hole it peaks in the
ultraviolet. Neither is visible. The peak temperature control maps the physical
profile onto the visible band so that its shape and the relative shifts can be
seen at all.

**No plasma physics.** There is no magnetohydrodynamics, no corona, no
Comptonisation, no synchrotron emission, no jet, and no absorption along the
line of sight. The disk is an opaque blackbody surface.

**The turbulence texture is decorative.** The banding is procedural noise
sheared by the real Keplerian rotation law, so the shear is physical and the
pattern is not.

**The star field is invented.** Its lensing, including the Einstein rings, is a
genuine output of the integration. The stars themselves are procedural, not a
catalogue.

**Finite escape radius.** Deflection accumulated beyond $r_{\mathrm{escape}}$ is
dropped. The residual is of order $M/r_{\mathrm{escape}}$, which is about half a
degree at the default setting of $140\,M$, and it decreases as the setting is raised.

**The lensing slider is not physics below 1.0.** It scales the $3Mu^{2}$ term for
comparison purposes only. The value 1.0 is Schwarzschild; the value 0.0 is
straight-line optics; anything in between solves nothing.

## 9. References

- K. Schwarzschild, *Über das Gravitationsfeld eines Massenpunktes nach der
  Einsteinschen Theorie*, Sitzungsberichte der Königlich Preussischen Akademie
  der Wissenschaften, 189, 1916.
- C. W. Misner, K. S. Thorne, and J. A. Wheeler, *Gravitation*, Freeman, 1973.
  Chapter 25 covers the orbit equation, the photon sphere, and local
  orthonormal frames.
- J. M. Bardeen, *Timelike and null geodesics in the Kerr metric*, in
  *Black Holes*, Les Houches 1972, Gordon and Breach, 1973. The photon capture
  cross-section and the $3\sqrt{3}\,M$ result.
- N. I. Shakura and R. A. Sunyaev, *Black holes in binary systems.
  Observational appearance*, Astronomy and Astrophysics 24, 337, 1973.
- J.-P. Luminet, *Image of a spherical black hole with thin accretion disk*,
  Astronomy and Astrophysics 75, 228, 1979. The first computed image of this
  configuration, and still the clearest description of why the disk appears
  above and below the hole at once.
- Event Horizon Telescope Collaboration, *First M87 Event Horizon Telescope
  Results*, Astrophysical Journal Letters 875, 2019.
- K. Narkowicz, *ACES filmic tone mapping curve*, 2015. The analytic
  approximation used for the tone curve.
- The Planckian locus is evaluated with a cubic approximation of the CIE 1931
  chromaticity coordinates, commonly attributed to Kim et al. (2002). That
  bibliographic attribution has not been verified directly and should be
  treated as unconfirmed. The fit itself has been checked against blackbody
  chromaticities over 1700 K to 25000 K.
