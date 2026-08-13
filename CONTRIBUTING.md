# Contributing

Thank you for considering a contribution. This project has one unusual
constraint that shapes everything else: it claims to solve physics rather than
to imitate it, and that claim has to stay true.

## The one hard rule

Any change that touches the integrator, the initial conditions, the frequency
shift, or the termination logic must be accompanied by the output of

```bash
python3 tools/verify_geodesics.py
```

showing that every check still passes. The workflow in
`.github/workflows/verify.yml` runs the same script, so a pull request that
breaks it will not go green. If your change alters the expected numbers on
purpose, say so explicitly in the pull request and explain why the new numbers
are the correct ones.

## Keeping the two implementations in agreement

The GPU shader in `index.html` and the NumPy renderer in
`tools/render_reference.py` implement the same algorithm twice, on purpose. A
change to one must be mirrored in the other. If they disagree, the images in
the README stop being a check on the shader and become decoration.

A quick way to compare after a change:

```bash
python3 tools/render_reference.py --scene edge --width 640 --ss 1
```

then open `index.html`, load the `Edge-on` preset, and compare.

## Scope

Contributions that fit this project well:

- The Kerr metric, as an option alongside Schwarzschild rather than a
  replacement. This is the single largest gap in the model.
- Better numerics, for example adaptive stepping keyed to `u`, or a higher
  order integrator with an error estimate.
- Performance work that lets more steps run per frame on integrated graphics.
- Spectral rendering, so that the observed colour follows from shifting a real
  spectrum rather than a blackbody temperature.
- Corrections to the physics or to the documentation. These are especially
  welcome and will be merged quickly.

Contributions that do not fit:

- Effects that improve the look at the cost of correctness, unless they are
  behind a clearly labelled switch and documented as non-physical in
  `docs/PHYSICS.md`, in the same way the lensing strength slider is.
- Build systems, bundlers, or frameworks. The simulation is one HTML file with
  no dependencies and it stays that way.

## Style

- JavaScript and GLSL follow the existing file: two space indentation, and
  comments that explain the physics rather than the syntax.
- Python targets 3.10 or later and follows PEP 8.
- Prose in documentation uses declarative sentences, no contractions, and the
  Oxford comma.

## Reporting a physics bug

Physics bugs are the most valuable issues this repository can receive. When you
open one, include the parameter values from the console, a screenshot if the
problem is visual, and, when you can, the analytic result you expected and its
source.
