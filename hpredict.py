#!/usr/bin/python
# -*- coding: utf-8 -*-
import ephem
import tle_util
import csv
import numpy as np
import copy
import argparse
import time

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

def find_passes(tle, gs_name, time_start, time_end, el_mask=0, search_step=60, pass_max_duration=1200):
    gs_loc = gs_locs[gs_name]
    # Initial search
    search_times=np.arange(time_start, time_end, search_step)
    search_coords=eph_az_el_range(tle, gs_loc, search_times)
    matching_indices=[i for i, x in enumerate(search_coords) if x[1] > 0]
    # Filter out consecutive indices
    last=-22
    unique_times=[]
    for ix in matching_indices:
        if ix-last > 1:
            unique_times.append(search_times[ix])
        last=ix
    # Now zoom in on each entry
    passes = []
    for ut in unique_times:
        times = np.arange(ut - search_step, ut + pass_max_duration)
        coords = eph_az_el_range(tle, gs_loc, times)
        p = {'gs':gs_name, 'sat_name':tle.sat_name, 'sat_no':tle.sat_no}
        max_el = 0
        p['t_start'] = 0
        p['t_stop'] = 0
        for i, t in enumerate(times):
            if coords[i][1] > max_el:
                max_el = coords[i][1]
            if coords[i][1] > 0 and p['t_start'] == 0:
                p['t_start'] = t
            if coords[i][1] < 0 and p['t_start'] > 0:
                p['t_stop'] = t
                break
        if max_el > el_mask:
            p['max_el'] = "%2.0f" % max_el
            passes.append(p)

    return passes

def combine_passes(passes):
    # Combine any passes that overlap
    sorted_passes=sorted(passes, key=lambda k: k['t_start'])
    combined_passes=[copy.copy(sorted_passes[0])]
    for p in sorted_passes[1:]:
        if combined_passes[-1]['t_stop'] >= p['t_start']:
            # p overlaps with the previous pass
            combined_passes[-1]['t_stop'] = p['t_stop']
            combined_passes[-1]['max_el'] += ", " + p['max_el']
            combined_passes[-1]['gs'] += ", " + p['gs']
        else:
            combined_passes.append(copy.copy(p))
    return combined_passes


def print_passes(passes):
    print "Start time (UTC)      Duration    Max elevation   Ground station"
    for p in passes:
        print "%s   %4.1f        %-16s%s" % (
            time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(p['t_start'])),
            (p['t_stop']-p['t_start'])/60.0, p['max_el'], p['gs'])


def main():
    parser = argparse.ArgumentParser(description='Pass prediction for ground station and satellite scheduling')
    parser.add_argument('-C', '--catalog', help='e.g. satcat.txt', default='norad.tle')
    parser.add_argument('-c', '--catno', help='e.g. 39515', type=int)
    parser.add_argument('-D', '--delay', help='hours to skip', default=0)
    parser.add_argument('-d', '--duration', help='Duration in days', default=4)
    parser.add_argument('gs', help='e.g. spokane,monterey=20')


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
            print "Couldn't find " + str(args.catno) + " in the catalog."
            exit(1)

    print "TLE:"
    print tle
    print

    t_start = time.time() + 3600 * float(args.delay)
    t_end = t_start + 86400 * float(args.duration)
    stations = args.gs.split(',')
    all_passes=[]
    for gs in stations:
        gss = gs.split('=')
        el_mask = 8
        if len(gss) == 2:
            el_mask = int(gss[1])
        passes = find_passes(tle, gss[0], t_start, t_end, el_mask=el_mask);
        all_passes += passes

    print "Combined pass list:"
    combined_passes = combine_passes(all_passes)
    if (len(combined_passes) > 19):
        combined_passes = combined_passes[0:19]

    print_passes(combined_passes)

    return 0

if __name__ == "__main__":
    main()
