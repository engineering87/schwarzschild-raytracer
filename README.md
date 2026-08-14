<div align="center">

# Schwarzschild Ray Tracer

**A black hole rendered by integrating the null geodesic equation, one ordinary differential equation per pixel, in real time in the browser.**

[![License: MIT](https://img.shields.io/badge/license-MIT-E8A33D.svg)](LICENSE)
[![Geodesic verification](https://github.com/engineering87/schwarzschild-raytracer/actions/workflows/verify.yml/badge.svg)](https://github.com/engineering87/schwarzschild-raytracer/actions/workflows/verify.yml)
[![Azure Static Web Apps](https://github.com/engineering87/schwarzschild-raytracer/actions/workflows/azure-static-web-apps.yml/badge.svg)](https://github.com/engineering87/schwarzschild-raytracer/actions/workflows/azure-static-web-apps.yml)
![WebGL 2](https://img.shields.io/badge/WebGL-2.0-blue)
![Dependencies](https://img.shields.io/badge/runtime%20dependencies-0-brightgreen)

<!-- Replace the URL below with the hostname Azure assigns, or with a custom domain. -->
### [Open the live simulation](https://schwarzschild-raytracer.azurestaticapps.net)

<img src="docs/media/edge.png" width="100%" alt="A black hole seen 10 degrees above its accretion disk. The disk appears to bend over and under the shadow, a thin photon ring hugs the shadow edge, and the approaching side is visibly brighter and bluer than the receding side.">

<sub>Observer at r = 60 M, 10 degrees above the disk plane. Rendered by <code>tools/render_reference.py</code>, which runs the same equations on the CPU.</sub>

</div>

---

## What this is

Black hole imagery is usually assembled the way any other visual effect is
assembled. A torus gets textured, the background gets bent by a lens
distortion, and the whole thing is adjusted until it convinces. That approach
works and it produces beautiful pictures, but the picture is a decision.

Here every pixel is the endpoint of a photon trajectory integrated backwards
through the Schwarzschild metric with fourth order Runge-Kutta. Whatever shows
up in the frame is what the integration produced. Nobody chose where the shadow
would end, how thick the photon ring would be, or which half of the disk would
be brighter.

The whole approach rests on a piece of luck about spherical symmetry. A light
ray in a Schwarzschild field can never leave the plane containing the observer
and its own direction, because there is no preferred direction for it to leave
towards. That collapses a three dimensional trajectory into a single equation
in the inverse radius $u = 1/r$:

$$\frac{d^{2}u}{d\varphi^{2}} + u = 3\left(\frac{GM}{c^{2}}\right)u^{2}$$

Drop the term on the right and what remains is a straight line written in polar
coordinates. That one term carries all of general relativity, and the renderer
integrates the equation exactly as written, which is why the familiar weak field
result $\alpha = 4GM/(c^{2}b)$ emerges on its own at large impact parameter
instead of being put in by hand.

## What you are looking at

The black disc in the middle is the shadow. Rays that reach $r < 2M$ cross the
horizon and never come back, so the pixels they came from stay dark. Its edge
falls at impact parameter $3\sqrt{3}\,M \approx 5.196\,M$, roughly two and a half
times the horizon radius, which is why the shadow looks considerably larger than
the hole itself.

The band arcing over the top of the shadow is the far side of the disk, visible
over the hole because the trajectories bend further than the inclination of the
disk. The band underneath is that same far side seen from below, through the
space under the hole. Both images exist at once, which Luminet worked out in
1979 with rather less computing power than a browser tab. Hugging the shadow
edge is a much thinner and brighter feature, the photon ring, made of rays that
wound around the photon sphere at $r = 3M$ before escaping towards the camera.

The left half of the disk is brighter and whiter because the material there is
coming towards you. At the innermost stable circular orbit the orbital speed is
exactly $c/2$ as measured by a local static observer, fast enough for
relativistic beaming to dominate the appearance. On the receding side the same
effect runs backwards and combines with gravitational redshift, pushing that
half towards orange. The faint circles scattered through the background are
Einstein rings, where the same stars are being imaged more than once by the same
gravitational lens.

That beaming is measurable, not just visible. `tools/measure_beaming.py` sums
the linear luminance of the two halves of the hero frame and reports the ratio,
and switching the Doppler factor off provides the control:

```
$ python3 tools/measure_beaming.py
approaching half       9431.3
receding half          2071.5
ratio                     4.55

$ python3 tools/measure_beaming.py --doppler off
approaching half       4458.2
receding half          4449.8
ratio                     1.00
```

With that term removed the frame goes symmetric to two decimal places, which
places the asymmetry squarely on the Doppler factor and not on the framing or
the geometry.

## Verified, not asserted

A renderer that claims to solve physics ought to prove it.
`tools/verify_geodesics.py` checks the integrator against two quantities with
exact closed forms, using the same arithmetic the shader runs, and it executes
on every push.

The first is the photon capture cross-section. Bisecting on the impact parameter
locates the boundary between capture and escape, and that boundary has to land
on $3\sqrt{3}\,M$, since it is the impact parameter of the unstable circular
photon orbit. The number appears nowhere in the source, so it has to come out of
the integration:

```
measured   b_crit = 5.196152423 M
analytic 3*sqrt(3) = 5.196152423 M
absolute error     = 1.78e-13
```

The second is light deflection, compared against the post-Newtonian expansion

$$\alpha = \frac{4M}{b} + \frac{15\pi}{4}\left(\frac{M}{b}\right)^{2} + \frac{128}{3}\left(\frac{M}{b}\right)^{3} + \cdots$$

| $b/M$ | measured $\alpha$ | $4M/b$ | through 2nd order | residual | 3rd order term |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 30 | 0.148248087 | 0.133333333 | 0.146423303 | 1.83e-03 | 1.58e-03 |
| 50 | 0.085083450 | 0.080000000 | 0.084712389 | 3.71e-04 | 3.41e-04 |
| 100 | 0.041222540 | 0.040000000 | 0.041178097 | 4.44e-05 | 4.27e-05 |
| 400 | 0.010074304 | 0.010000000 | 0.010073631 | 6.73e-07 | 6.67e-07 |

What is left over after the second order term follows the third order term to
about one percent, which is how a correct integration truncated at a known order
should behave. Cutting the step from 0.004 to 0.0005 shifts the answer by 8e-10
radians, so what remains is series truncation and not numerical error.

## Gallery

Every image below comes out of the same code path, and each pair differs by a
single switch.

<table>
<tr>
<td width="50%"><img src="docs/media/face.png" alt="Face-on view"></td>
<td width="50%"><img src="docs/media/ring.png" alt="Close view of the photon ring"></td>
</tr>
<tr>
<td><b>Face-on.</b> Looking straight down the disk axis, beaming disappears
because nothing moves along the line of sight, and the photon ring closes into a
complete circle.</td>
<td><b>Close to the plane at r = 17 M.</b> The photon ring pulls away from the
shadow edge, and background stars become visible in the gap between them.</td>
</tr>
<tr>
<td><img src="docs/media/nodisk.png" alt="The star field alone, lensed"></td>
<td><img src="docs/media/flat.png" alt="The same scene with the lensing term disabled"></td>
</tr>
<tr>
<td><b>Lensing on its own.</b> With the disk switched off the concentric arcs
stand out clearly. They are the same background stars imaged repeatedly around
the shadow.</td>
<td><b>Lensing switched off.</b> Setting the $3Mu^{2}$ term to zero sends every
ray along a straight line, which is how the same disk would look under Newtonian
optics. It is a comparison mode and solves nothing.</td>
</tr>
<tr>
<td><img src="docs/media/nodoppler.png" alt="Doppler term disabled"></td>
<td><img src="docs/media/noredshift.png" alt="Gravitational redshift disabled"></td>
</tr>
<tr>
<td><b>Doppler term disabled.</b> The frame goes left-right symmetric, which
attributes the entire asymmetry of the hero image to this one factor.</td>
<td><b>Gravitational redshift disabled.</b> The inner disk brightens and shifts
blue once the climb out of the potential well stops being paid for.</td>
</tr>
</table>

## Running it

The simulation is a single self-contained HTML file with no build step, no
bundler, and nothing to install. Clone the repository and open `index.html`, or
serve the directory if your browser is fussy about local files:

```bash
git clone https://github.com/engineering87/schwarzschild-raytracer.git
cd schwarzschild-raytracer
python3 -m http.server 8000
```

Then visit <http://localhost:8000>. A WebGL 2 context is required.

Drag to orbit, scroll to change the observer radius, and use the console on the
right for everything else. While the camera sits still the frame accumulates
jittered samples and reports `converged` once it settles, so leaving it alone for
a few seconds gives you a clean image worth capturing. The `Save PNG` button
writes out whatever is currently on screen.

Cost scales roughly as pixels times steps, and rays that escape or hit the disk
stop early, so the defaults run interactively at 1080p on a discrete GPU. On
integrated graphics, drop `Render scale` to 0.6 and `Integration steps` to 400
before touching anything else. Neither one changes the physics, only how finely
and how far each ray is followed.

## Deployment

Pushing to `main` publishes the simulation to Azure Static Web Apps through
`.github/workflows/azure-static-web-apps.yml`. Only `index.html` and
`staticwebapp.config.json` are staged and uploaded, which keeps the deployed
payload under 100 kB while the images, the offline renderer, and the
documentation stay in the repository without being served.

Setting this up on a fresh Azure resource takes three steps. Create the Static
Web App, choosing the deployment source "Other" so that Azure does not generate
a second workflow of its own:

```bash
az staticwebapp create \
  --name schwarzschild-raytracer \
  --resource-group <your-resource-group> \
  --location westeurope \
  --sku Free
```

Read the deployment token:

```bash
az staticwebapp secrets list \
  --name schwarzschild-raytracer \
  --query "properties.apiKey" -o tsv
```

Then store it in the repository under Settings, Secrets and variables, Actions,
as `AZURE_STATIC_WEB_APPS_API_TOKEN`, and push. Preview environments for pull
requests are deliberately left unconfigured, since a single page gains little
from them and the reference renderer under `tools/` already provides a way to
inspect a change before it lands.

`staticwebapp.config.json` sets caching, a content security policy that allows
only the inline script and the web font, and a fallback that routes everything
to the simulation.

## Reproducing the images

Every picture in this README is generated from source by a NumPy
reimplementation of the same algorithm, so nothing here is an artefact that
cannot be regenerated on a machine with no GPU and no browser:

```bash
pip install -r tools/requirements.txt
python3 tools/render_reference.py --list
python3 tools/render_reference.py --scene edge --width 1280 --ss 2
```

The reference renderer earns its place for a second reason. If a change to the
shader makes the GPU output drift away from the CPU output, one of the two is
wrong, and having both makes the disagreement visible instead of leaving it
plausible.

## What is not modelled

The largest limitation by far is that the hole does not spin. This is
Schwarzschild rather than Kerr, so there is no frame dragging and no ergosphere.
Real holes almost certainly rotate, and the difference is not cosmetic: for a
maximally spinning hole the innermost stable circular orbit moves from $6M$ down
to $M$ for prograde orbits, which changes the temperature profile and the shape
of the shadow together.

Colour is a mapping rather than a measurement. A real disk peaks in the
ultraviolet around a supermassive hole and in soft X-rays around a stellar mass
one, so none of it would reach your eye at all. The peak temperature control
projects the physical profile onto the visible band. The shape of that profile
is physics, the absolute temperature is a display choice, and the interface says
as much.

There is no plasma physics anywhere in this. No magnetohydrodynamics, no corona,
no Comptonisation, no synchrotron emission, no jet, and no absorption along the
line of sight. The disk behaves as an opaque blackbody surface and nothing more.
The turbulent banding across it is procedural noise sheared by the real Keplerian
rotation law, so the shear is physical while the pattern is decoration. The star
field is likewise invented: its lensing is a genuine output of the integration,
but the stars themselves are procedural rather than a catalogue.

Two numerical caveats are worth knowing. Deflection accumulated beyond the escape
radius is discarded, leaving a residual of order $M/r_{\mathrm{escape}}$, roughly
half a degree at the default setting and smaller as you raise it. And the lensing
slider stops being physics as soon as it leaves 1.0, since it simply scales the
$3Mu^{2}$ term for the sake of comparison.

The full discussion, with derivations, lives in
[docs/PHYSICS.md](docs/PHYSICS.md).

## Repository layout

```
index.html                    the simulation, self-contained, no build step
staticwebapp.config.json      headers, caching, and routing for Azure
docs/PHYSICS.md               derivations, the frequency shift, verification results
docs/PROVENANCE.md            how this was authored, and how to compare other models
docs/media/                   every image in this README, all regenerable
tools/render_reference.py     NumPy reimplementation used to produce the images
tools/verify_geodesics.py     numerical checks against exact closed forms
tools/measure_beaming.py      measures the Doppler asymmetry, with a control
.github/workflows/            verification on every push, deployment on main
```

## Provenance

All of the code, the images, and the documentation in this repository were
produced by Anthropic Claude Opus 5 during a single session on 13 August 2026,
starting from a one sentence brief that named no metric, no integration scheme,
no disk model, and no verification strategy. The human contribution was the
brief, the direction, and the review.

This is written down because the repository is meant to serve as the reference
point of a comparison: the same brief will go to other models, and the results
will be set side by side. [docs/PROVENANCE.md](docs/PROVENANCE.md) has the exact
brief, the split between what was verified and what was not, the course
corrections made along the way including the mistakes, and a checklist of the
specific places where a plausible looking black hole renderer can be quietly
wrong. The verification scripts under `tools/` are deliberately independent of
everything else, so another implementation can be dropped into
`tools/verify_geodesics.py` and graded on numbers.

Equations are typeset rather than approximated. The Markdown uses the LaTeX
support built into GitHub, and the simulation typesets its own formulas in HTML
and CSS, with real fractions, radicals, and raised exponents, which keeps the
page free of any external typesetting library at runtime.

## References

The physics is standard and old. The only novelty is that it runs at sixty
frames per second in a tab.

- K. Schwarzschild, Sitzungsberichte der Preussischen Akademie der
  Wissenschaften, 189, 1916.
- C. W. Misner, K. S. Thorne, and J. A. Wheeler, *Gravitation*, Freeman, 1973.
- J. M. Bardeen, in *Black Holes*, Les Houches 1972, Gordon and Breach, 1973.
- N. I. Shakura and R. A. Sunyaev, Astronomy and Astrophysics 24, 337, 1973.
- J.-P. Luminet, Astronomy and Astrophysics 75, 228, 1979.
- Event Horizon Telescope Collaboration, Astrophysical Journal Letters 875, 2019.

One citation carries a warning. The Planckian locus is evaluated with a cubic
approximation of the CIE 1931 chromaticity coordinates commonly attributed to
Kim et al. (2002), and that bibliographic reference has not been checked
directly, so treat it as unconfirmed. The fit itself has been validated against
blackbody chromaticities from 1700 K to 25000 K.

## Contributing

Issues and pull requests are welcome, and [CONTRIBUTING.md](CONTRIBUTING.md)
covers the details. One rule outweighs the rest: any change that touches the
physics has to arrive with the output of `tools/verify_geodesics.py` showing that
the checks still pass.

## Citing this work

See [CITATION.cff](CITATION.cff), or use the *Cite this repository* button in the
GitHub sidebar.

## License

MIT. See [LICENSE](LICENSE).
