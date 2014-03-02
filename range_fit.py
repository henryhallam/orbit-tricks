#!/usr/bin/python
# -*- coding: utf-8 -*-
import ephem
import tle_util
import csv
import numpy as np
import copy
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import argparse

max_plausible_rms_range_err = 100.0

gs_locs = {'monterey' : (36.6, -121.9, 8),
           'spokane'  : (47.659, -117.425, 562)}

# tle: tle_util.TLE class
# latlonel: (lat, lon, el) of ground station in degrees and meters
# times: list of unix times
# returns list of ranges in km
def eph_ranges(tle, latlonel, times):
    from math import radians
    eph = ephem.readtle(tle.sat_name, tle.line1(), tle.line2())
    r = []
    gs = ephem.Observer()
    gs.lat = radians(latlonel[0])
    gs.lon = radians(latlonel[1])
    gs.elevation = radians(latlonel[2])
    for t in times:
        gs.date = (t/86400.0) + ephem.Date('1970/1/1 0:00')
        eph.compute(gs)
        r.append(eph.range / 1000.0)
    return r

def load_ranges(filename, require_valid_crc = True):
    fin = open(filename, 'r')
    reader = csv.reader(fin)
    ranges = []
    for row in reader:
        try:
            if int(row[2]) == 1 or require_valid_crc == False:
                ranges.append((float(row[0]), float(row[1])))
        except:
            pass
    fin.close()
    return ranges

# Return the sum of the squares of the differences in ranges between a TLE and some observations
# obs: list of ((lat, lon, el), [(time, range)])
def sum_err_sq(tle, obs):
    from operator import add
    ob_r = []
    pred_r = []
    for gs, timesranges in obs:
        ob_t = [ t for t, r in timesranges ]
        ob_r = ob_r + ([ r for t, r in timesranges ])
        pred_r = pred_r + eph_ranges(tle, gs, ob_t)

    return reduce(add, map(lambda x, y : (x-y)**2, ob_r, pred_r))

def rms_error(tle, obs):
    from math import sqrt
    obslen = sum([ len(trs) for (gs, trs) in obs ])
    return sqrt(sum_err_sq(tle, obs) / obslen)

def optimize(tle_prior, obs, freevars={'M'}, quiet=False):
    from scipy.optimize import fmin
    tle = copy.copy(tle_prior)

    def score(x):
        x = list(x)
        if 'M' in freevars: tle.mean_anom = x.pop()
        if 'i' in freevars: tle.inclination = x.pop()
        if '☊' in freevars: tle.raan = x.pop()
        if 'n' in freevars: tle.mean_motion = x.pop()
        if 'ω' in freevars: tle.arg_pe = x.pop()
        if 'e' in freevars: tle.ecc = x.pop()
        if 'b' in freevars: tle.bstar = x.pop()

            #        if tle.ecc < 0:
            #            tle.ecc = 0

        return rms_error(tle, obs)

    if not quiet:
        print 'Attempting to fit by varying the following parameters: ',
        for var in freevars: print var + " ",
        print
    x0 = []
    if 'M' in freevars: x0.insert(0, tle.mean_anom)
    if 'i' in freevars: x0.insert(0, tle.inclination)
    if '☊' in freevars: x0.insert(0, tle.raan)
    if 'n' in freevars: x0.insert(0, tle.mean_motion)
    if 'ω' in freevars: x0.insert(0, tle.arg_pe)
    if 'e' in freevars: x0.insert(0, tle.ecc)
    if 'b' in freevars: x0.insert(0, tle.bstar)

    result = fmin(score, x0, disp = False, maxiter = 500, full_output = True)
    if (result[4] != 0):
        print 'Failed to converge'
        return tle_prior
    if not quiet:
        print 'Improved RMS error from %.1f km to %.1f km by adjusting parameters\nfrom %s\n  to %s' % (
            rms_error(tle_prior, obs), result[1], x0, result[0])
    if result[1] > max_plausible_rms_range_err:
        print 'Converged, but RMS error is still implausibly large.'
        print 'Check you have the right satellite and ground station?'
        return tle_prior
    return tle

def plot_tle_obs(tle, obs, color):
    for ob in obs:
        trs = ob[1]
        t = [ a for (a, b) in trs ]
        r = [ b for (a, b) in trs ]
        t_shift = [time-t[0] for time in t]
        plt.plot(t_shift, r, '+b')
        pred_r = eph_ranges(tle, ob[0], t)
        plt.plot(t_shift, pred_r, '-' + color)
        plt.xlabel('Time since start of each pass / s')
        plt.ylabel('Range / km')


def main():
    parser = argparse.ArgumentParser(description='Orbit determination based on LST ranging')
    parser.add_argument('catalog', help='e.g. satcat.txt')
    parser.add_argument('-c', '--catno', type=int, help='e.g. 39512')
    parser.add_argument('ranges', nargs='+', help='e.g. monterey=dove2-ranges-monterey.txt')
    parser.add_argument('-M', '--mean-anom', help='fit the mean anomaly (M).', const='M',
                        action='append_const', dest='fitvars')
    parser.add_argument('-r', '--raan', help='fit the right ascension of ascending node (☊)', const='☊',
                        action='append_const', dest='fitvars')
    parser.add_argument('-a', '--argpe', help='fit the argument of periapsis (ω)', const='ω',
                        action='append_const', dest='fitvars')
    parser.add_argument('-i', '--inc', help='fit the inclination', const='i',
                        action='append_const', dest='fitvars')
    parser.add_argument('-n', '--mean-motion', help='fit the mean motion', const='n',
                        action='append_const', dest='fitvars')
    parser.add_argument('-e', '--ecc', help='fit the eccentricity', const='e',
                        action='append_const', dest='fitvars')
    parser.add_argument('-b', '--bstar', help='fit the drag term', const='b',
                        action='append_const', dest='fitvars')
    parser.add_argument('-f', '--full', help='fit all elements', const=['M','☊','ω','i','n','e','b'],
                        action='store_const', dest='fitvars')

    args = parser.parse_args()
    tles = tle_util.load_catalog(args.catalog)

    if args.catno is None:
        if len(tles) > 1:
            print "More than one satellite in the catalog, therefore you must specify"
            print "which one to fit, using the '-c' option.  e.g. -c 39512"
            exit(1)
        else:
            tle = tles.values()[0]
    else:
        try:
            tle = tles[args.catno]
        except:
            print "Couldn't find '" + str(args.catno) + "' in the catalog."
            exit(1)

    print "Initial TLE:"
    print tle

    obs = []
    for rangeset in args.ranges:
        print rangeset
        [gs_locname, rangefile] = rangeset.split('=')
        obs.append((gs_locs[gs_locname], load_ranges(rangefile)))

    print "Loaded %s ranges" % [ len(trs) for (gs, trs) in obs ]
    print "Initial RMS error: %.1f km" % rms_error(tle, obs)

    if args.fitvars is None:
        args.fitvars = ['M']

    plot_tle_obs(tle, obs, 'r')

    new_tle = optimize(tle, obs, freevars = set(args.fitvars))

    plot_tle_obs(new_tle, obs, 'g')
    fig = plt.gcf()
    fig.set_size_inches(18.5,10.5)
    plt.savefig("plot.png")
    plt.close()

    if (str(new_tle) == str(tle)):
        print "TLE unchanged, it is:"
        print tle
        return 1
    else:
        print "Improved TLE:"
        print new_tle
        return 0
    return 0

if __name__ == "__main__":
    main()
