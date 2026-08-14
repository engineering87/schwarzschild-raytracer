# Provenance

This document records how the code in this repository was produced, by whom or
by what, and which parts of it were checked rather than merely asserted. It
exists because the repository doubles as the reference point of a comparison
study. The same brief will go to other language models, and any comparison only
means something if the starting conditions were written down before anyone knew
how the results would turn out.

## Summary

| Field | Value |
| --- | --- |
| Model | Anthropic Claude Opus 5 |
| Interface | Claude web chat, with code execution and file creation enabled |
| Date of the session | 13 August 2026 |
| Working language of the conversation | Italian |
| Language of all produced artefacts | English |
| Human role | Brief, direction, and review |
| Model role | All code, documentation, calibration, and verification |

## The brief

The session began with one sentence, in Italian, with no further specification.

> vorrei creare una simulazione di un buco nero che giri nel browser, la
> simulazione deve essere professionale, accattivante e seguire le leggi della
> fisica conosciuta

Translated: *I would like to create a black hole simulation that runs in the
browser. The simulation must be professional, visually compelling, and follow
the laws of known physics.*

A standing instruction ran for the whole session, requiring that every claim be
verifiable, that sources be cited, and that anything unconfirmable be marked as
such. The warning attached to the Planckian locus attribution, which appears in
three separate places, comes directly from that instruction.

A second message, later in the same session, asked for the work to be turned
into a complete open source repository with a README and a screenshot. No
technical direction was given at any point: neither the metric, nor the
integration scheme, nor the disk model, nor the verification strategy, nor the
visual design were specified by the human.

## What the model produced

Everything in this repository. Specifically:

- The WebGL 2 simulation in `index.html`, including the GLSL integrator, the
  frequency shift derivation, the accumulation and tone mapping pipeline, and
  the interface design.
- The NumPy reference renderer in `tools/render_reference.py`, and the seven
  images in `docs/media`, which are its output.
- The verification scripts in `tools/verify_geodesics.py` and
  `tools/measure_beaming.py`.
- All documentation, including this file.

## What was actually verified

Everything below was computed during the session and can be reproduced by
running the scripts, which is what separates a checked claim from a claim.

**The critical impact parameter.** Bisection on the impact parameter separates
captured from escaping rays. The measured boundary is $5.196152423\,M$ against
the analytic value $3\sqrt{3} = 5.196152423$, an absolute error of
$1.8 \times 10^{-13}$. This is a
strong test because the number is not present anywhere in the source: it has to
emerge from the integration.

**The light deflection series.** The measured bending was compared with
$\alpha = 4M/b + \tfrac{15\pi}{4}(M/b)^{2} + \tfrac{128}{3}(M/b)^{3}$. The residual after the second order
term tracks the third order term to about one percent at large impact
parameter. Halving the integration step moves the result by 8e-10 radians, so
the remaining discrepancy is series truncation rather than numerical error.

**The beaming asymmetry, with a control.** The approaching half of the default
frame is 4.55 times brighter than the receding half. With the Doppler factor
disabled the same measurement returns 1.00. The control is the informative
half: it attributes the asymmetry to that single term rather than to the
framing or the geometry.

**The sign of the beaming.** The sign of the axial impact parameter
$\lambda = -b\,\hat{n}_{z}$ was derived analytically during the session by placing an observer
on the positive x axis and checking which side of the disk moves towards it. An
initial derivation had the sign inverted, which would have put the bright side
on the wrong half of the image, and was corrected before any code was written.

## What was not verified

- The GPU shader was never executed. The sandbox has no WebGL context, so
  `index.html` was checked for JavaScript syntax and for algorithmic agreement
  with the CPU implementation, but not run. The images in the README come from
  the CPU renderer, not from a browser screenshot.
- The bibliographic attribution of the Planckian locus fit to Kim et al. (2002)
  is unconfirmed and is marked as such wherever it appears.
- No comparison was made against published reference images or against
  observational data.

## Course corrections during the session

A comparison that reports only the finished artefact throws away most of the
signal, so the failures are recorded here alongside the successes.

1. **A garbled expression in the readout code.** The first version of the
   maximum blueshift calculation in `index.html` contained a leftover fragment
   that multiplied a term by zero and added it back. It was found and rewritten
   before delivery.
2. **The sign of the axial impact parameter.** Described above. Caught during
   derivation.
3. **The bloom radius did not scale with resolution.** The first CPU render
   applied a blur sized in absolute pixels, which washed the whole frame out at
   low resolution. Fixed by defining the radius against a reference frame
   width.
4. **The first high resolution render exhausted memory.** Rendering 3.7 million
   rays at once with a dozen float64 arrays per ray does not fit in the
   available memory. Fixed by rendering in horizontal bands, which was then
   checked for seams: the mean row-to-row difference at band boundaries is 1.18
   against a frame average of 1.33, so there is no discontinuity.
5. **Four rounds of framing calibration.** The initial default view cropped the
   disk and saturated to white. The observer radius, field of view, peak
   temperature, and exposure were tuned across four rendered comparison sheets
   before the defaults were fixed. The physics did not change; only the camera
   and the display mapping did.

## Notes for a model comparison

If you are reproducing this with another model, the following make the
comparison informative rather than aesthetic.

Ask the same question and offer no technical direction. What you want to learn
is whether the model reaches for the exact orbit equation of its own accord, or
settles for a screen-space distortion, a weak-field approximation applied to a
straight ray, or a hand-tuned lens shader.

Then work through the checks below. Each row marks a place where a
plausible-looking implementation can be quietly wrong.

| Check | What a correct implementation does |
| --- | --- |
| The equation integrated | $\dfrac{d^{2}u}{d\varphi^{2}} + u = 3Mu^{2}$, or an equivalent exact formulation, rather than a deflection formula applied once |
| Observer frame | Includes the $\sqrt{1 - 2M/r}$ factor when converting the view direction into initial conditions |
| Measured $b_{\mathrm{crit}}$ | $3\sqrt{3}\,M$, emerging from the integration rather than hard-coded |
| Deflection at large $b$ | Matches the post-Newtonian series beyond first order |
| Frequency shift | $g = \dfrac{\sqrt{1 - 3M/r}}{1 - \Omega\lambda}$ for circular Keplerian orbits |
| Sign of the beaming | The bright side is the one whose material approaches the observer |
| Intensity scaling | $I_{\mathrm{obs}} = g^{4} I_{\mathrm{em}}$, not $g^{2}$ or $g^{3}$ |
| Disk profile | Vanishes at the inner edge and peaks at $\tfrac{49}{36}\,r_{\mathrm{in}}$ |
| Secondary image | The far side of the disk appears both above and below the shadow |
| Photon ring | A distinct thin feature at the shadow edge, not the disk edge |
| Honesty of the documentation | States which parts are physical and which are display choices |

Run the verification scripts against the other integrator. The two scripts in
`tools/` were kept independent of the rest of the project for exactly this
purpose, and porting another implementation into the `integrate` function of
`tools/verify_geodesics.py` takes a few minutes while producing a number rather
than an impression.

Finally, keep correctness and appearance on separate ledgers. A model can
produce a beautiful image from wrong physics, and a correct integrator saddled
with a badly chosen camera and exposure will look worse than a shader trick.
Grade the two axes apart, and note how many iterations each one took to get
right.
