#!/usr/bin/python
# -*- coding: utf-8 -*-
import ephem
import tle_util
import csv
import numpy as np
import copy
import argparse
import time
import math

# Insert your ground station locations here
# 'name' : (lat, lon, alt)
# with lat,lon in degrees and alt in meters
gs_locs = {'monterey' : (36.6, -121.9, 8),
           'spokane'  : (47.659, -117.425, 562)}

# tle: tle_util.TLE class
# latlonel: (lat, lon, el) of ground station in degrees and meters
# times: list of unix times
# returns list of (az, el, range)
def eph_az_el_range(tle, latlonel, times):
    from math import radians, degrees
    eph = ephem.readtle(tle.sat_name, tle.line1(), tle.line2())
    r = []
    gs = ephem.Observer()
    gs.pressure=0
    gs.lat = radians(latlonel[0])
    gs.lon = radians(latlonel[1])
    gs.elevation = radians(latlonel[2])
    for t in times:
        gs.date = (t/86400.0) + ephem.Date('1970/1/1 0:00')
        eph.compute(gs)
        r.append((degrees(eph.az), degrees(eph.alt), eph.range / 1000.0))
    return r

def main():
    parser = argparse.ArgumentParser(description='Annotates logfiles with time, elevation, range')
    parser.add_argument('logfile', help='e.g. hsdrxmux.log')
    parser.add_argument('-g', '--groundstation', help='e.g. monterey, spokane', required=True)

    args = parser.parse_args()
    tles = tle_util.load_catalog("norad.tle")

    tle = tles[39429]
#    print "TLE:"
#    print tle
#    print

    log_entries=[]
    times=[]
    for row in open(args.logfile, "r"):
        times.append(float(row[2:17]))
        log_entries.append(row[18:])

    aers=eph_az_el_range(tle, gs_locs[args.groundstation], times)
    print "Time, Elevation, Range from " + args.groundstation + ", Log entry"
    for i, t in enumerate(times):
        print time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(round(t))) + \
          ", %4.1f, %4.0f, "%(aers[i][1], aers[i][2]) + log_entries[i],

    return 0

if __name__ == "__main__":
    main()
