#!/usr/bin/env python
"""
This is a Python script that turns a stipple file into a .flp

The source file should be generated by stippler.py
"""

from math import ceil
import json
import argparse

# This file lives in examples/stipple
import sys
sys.path.append('../..')

import numpy as np

import OpenFL.FLP as F

def mm_to_pos(p):
    """ Converts a position in mm in the range +/- 62.6
        into a galvo tick value in the range 0, 65535
    """
    return int(np.interp(p, (-125/2., 125/2.), (0, 0xffff)))


def to_flp(stipples, dpi=300, x_mm=0, y_mm=0, laser_pwr=35000,
           ticks=500, base=100):
    """" Converts a set of stipples into a list of FLP packets
            dpi is the image's DPI
            x_mm and y_mm are the corner location of the image (default 0,0)
                (where 0,0 is the center of the build platform)
            laser_power is the laser's power level in ticks
            ticks is the number of frames the laser spends a black point
            base is the number of frames the laser spends on a white point
    """
    # Accumulated list of FLP packets
    packets = F.Packets()

    # Sort by X to reduce the amount of laser moves necessary
    stipples = sorted(stipples, key=lambda s: s[0])

    # Draw stuff for every point
    for x, y, i in stipples:
        # Center position in mm
        x = mm_to_pos(x / float(dpi) * 25.4 + x_mm)
        y = mm_to_pos(y / float(dpi) * 25.4 + y_mm)

        # Decide how long to stay on this point (longer time = darker point)
        t = int(ceil((ticks - base) * (1 - i)) + base)
        if t == 0:
            continue

        # Move to this stipple's location with the laser off, then pause
        # briefly to let the controller stabilize
        packets.append(F.LaserPowerLevel(0))
        packets.append(F.XYMove([[x, y, 200], [x, y, 100]]))

        # Draw the spot with the laser on
        packets.append(F.LaserPowerLevel(laser_pwr))
        packets.append(F.XYMove([[x, y, t]]))

    return packets

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert stipple data to a .flp file")
    parser.add_argument('-dpi', metavar='dpi', type=int, default=300,
                        help='Image resolution in dots per inch')
    parser.add_argument('-x', metavar='x', type=int, default=0,
                        help="Image corner's x location (in mm)")
    parser.add_argument('-y', metavar='y', type=int, default=0,
                        help="Image corner's y location (in mm)")
    parser.add_argument('input', metavar='input', type=str,
                        help='source stipple file (created by stippler.py)')
    parser.add_argument('output', metavar='output', type=str,
                        help='output file (should be a .flp)')
    args = parser.parse_args()

    stipples = json.load(open(args.input))['stipples']
    out = to_flp(stipples, dpi=args.dpi, x_mm=args.x, y_mm=args.y)
    out.tofile(args.output)
