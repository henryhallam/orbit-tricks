Orbit utilities
===============

A selection of minor hacks for space wizards, comprising:

 * range_fit.py:    Take an imperfect TLE and massage it to fit radio ranging data
 * hpredict.py:     Compute a schedule of ground station passes, suitable for 
                    feeding the satellite or certain ground stations
 * azelrange.py:    Annotate log files with the angle and distance to the sat.
 * Orbit differences.ipynb: 
                    An IPython notebook illustrating how you can quantify the
                    difference between two TLEs (illustrating the volatility of
                    Space Track's issued orbits)
 * tle_util.py:     TLE parser library used by the above.
 * scrape_track.sh: Pull the latest TLE from JSpOC.

Authors
-------
[Henry](mailto:henry@planet-labs.com)

Installation
------------
Sorry, no distutils yet.
'Orbit differences' is an ipython notebook, so install ipython to use it.

You'll want (probably via pip): numpy, scipy, matplotlib, pyephem

Also download https://pypi.python.org/packages/source/s/sgp4/sgp4-1.1.tar.gz
and extract it into this directory.

If you want to use scrape_track, edit it to include your Space Track credentials.


Operation
---------
### range_fit
Obtain a TLE that you wish to improve.  This could be a prelaunch prediction from
a launch provider, an out-of-date Space Track TLE, etc.  Put it in a file.
If it's in 3-line format, great.  Otherwise prepend a line with the name of the
spacecraft.
If you want, you can have more than one satellite in the file, but they must have
unique names.
e.g.

  ./scrape_track.sh
   (...)
  cat norad.tle
  0 DOVE 3
  1 39429U 13066P   14036.66224386  .00001774  00000-0  34640-3 0   646
  2 39429 097.7753 109.2910 0154894 310.7235 048.0617 14.56764061 11098

Obtain some LST ranging data.  This can be obtained via lst_ctl -R. Save the
output to a file.  Remember which ground station the ranging was run from.

You can collect one or several passes worth of data, from one or several ground
stations.  Put each set in a separate file. Each pass should have at least 20 points
to be useful.

One pass is sufficient to fit the mean anomaly; 2 to fit the mean motion; 3 or 4
passes are suggested if trying to fit all the orbital elements.

Run range_fit:

  ./range_fit.py <TLEfile> <gs=rangefile> [gs=rangefile] [optional args] ...

TLEfile is the catalog containing one or more TLEs.  You can only improve one at
a time even if there are several in the file.  The file will not be modified by
range_fit.

Each set of ranging data is specified as gs=rangefile where 'gs' is
the name of the ground station (their names and locations are
hardcoded in the source) and 'rangefile' is the name of a file
containing the range data as output by lst_ctl.

If the TLE catalog contains more than one satellite, you must tell range_fit which
satellite you're interested in with the '-s' argument.

By default, range_fit will only try to fit the mean anomaly.  You can tell it to
fit all the parameters with the '-f' flag, or tell it exactly which ones to fit
with other flags (range_fit.py -h for full info)

The output should be pretty self-explanatory.  If you can get the RMS error down
to < 5 km, that's pretty good (LST ranging RMS noise is around 3 km).  But beware
the ill-conditioned problem - if you fit all parameters with only one pass' worth
of ranging data, the RMS error will be small but the orbit will probably be bogus.


### hpredict
e.g.

 ./hpredict.py -c norad.tle monterey,spokane,timbuktu=25

Lists passes for 3 ground stations with Monterey and Spokane having default
elevation mask of 8 degrees, Timbuktu a higher mask of 25 degrees
