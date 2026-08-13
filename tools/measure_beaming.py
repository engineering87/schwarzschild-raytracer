#!/usr/bin/env python3
"""
Measure the relativistic beaming asymmetry of a rendered frame.

The claim in the README, that the approaching half of the disk is several
times brighter than the receding half, is a number rather than an impression.
This script produces it. It renders a scene at low resolution with the CPU
reference implementation, sums the linear luminance of the two halves of the
frame, and reports the ratio.

Running it with --doppler off should return a ratio very close to 1.0, because
the frame becomes left-right symmetric once beaming is removed. That control is
the point of the script: it shows the asymmetry comes from the Doppler factor
and not from the geometry.

Usage:
    python tools/measure_beaming.py
    python tools/measure_beaming.py --scene edge --doppler off
"""

import argparse
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import render_reference as rr  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="edge")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--doppler", choices=("on", "off"), default="on")
    args = parser.parse_args()

    scene = rr.SCENES[args.scene]
    scene.doppler = args.doppler == "on"
    height = int(round(args.width / scene.aspect))

    hdr = rr.trace(scene, args.width, height, verbose=False)
    luminance = hdr.mean(axis=-1)
    half = args.width // 2
    approaching = float(luminance[:, :half].sum())
    receding = float(luminance[:, half:].sum())

    print(f"scene            {scene.name}")
    print(f"doppler          {'on' if scene.doppler else 'off'}")
    print(f"approaching half {approaching:12.1f}")
    print(f"receding half    {receding:12.1f}")
    print(f"ratio            {approaching / max(receding, 1e-9):12.2f}")


if __name__ == "__main__":
    main()
