# tle_util.py - reading and writing Two Line Elements
# Henry Hallam 2013, henry@pericynthion.org

import time, calendar

def _linesum(tle_line):
    n = 0
    for d in tle_line:
        if d.isdigit():
            n = n + int(d)
        elif d == '-':
            n = n + 1
    return str(n % 10)

class TLE:

    def __init__(self, TLE, ignore_checksum=False):
        #print "Groking TLE for '" + TLE[0] + "'"
        # A little sanity checking on the input
        for n in range(1,3):
            if len(TLE[n]) != 69:
                raise ValueError("Line %d has %d characters, should be 69"
                                 % (n,len(TLE(n))))
            if not ignore_checksum:
                cksum = _linesum(TLE[n][:-1])
                if TLE[n][-1] != cksum:
                    raise ValueError("Line %d ends in '%c', should be '%c'"
                                     % (n, TLE[n][-1], cksum))

        self.sat_name = TLE[0].strip()
        if self.sat_name[0:2] == "0 ":
            self.sat_name = self.sat_name[2:]

        self.sat_no = int(TLE[1][2:7])
        self.classification = TLE[1][7]
        self.intl_des = TLE[1][9:17]
        year2dig = int(TLE[1][18:20])
        if year2dig < 57:
            self.epoch_year = year2dig + 2000
        else:
            self.epoch_year = year2dig + 1900
        self.epoch_jday = float(TLE[1][20:32])
        self.mean_motion_deriv_1 = 2 * float(TLE[1][33:43])
        self.mean_motion_deriv_2 = 6E-5 * float(TLE[1][44:50] + "E" + TLE[1][50:52])
        self.bstar = 1E-5 * float(TLE[1][53:59] + "E" + TLE[1][59:61])
        try:
            self.el_set_no = int(TLE[1][64:68])
        except ValueError:
            self.el_set_no = 0

        if int(TLE[2][2:7]) != self.sat_no:
            raise ValueError("Sat no on line 2: '%s' doesn't match that parsed from line 1: %d"
                             %(TLE[2][2:7], self.sat_no))
        self.inclination = float(TLE[2][8:16])
        self.raan = float(TLE[2][17:25])
        self.ecc = float("."+TLE[2][26:33])
        self.arg_pe = float(TLE[2][34:42])
        self.mean_anom = float(TLE[2][43:51])
        self.mean_motion = float(TLE[2][52:63])
        self.rev_no = int(TLE[2][63:68])

    def line1(self):
        l = "1 %05d%c %8.8s " % (self.sat_no, self.classification, self.intl_des)
        l = l + "%02d%12.8f " % (self.epoch_year % 100, self.epoch_jday)
        tmp = "%11.8f" % (self.mean_motion_deriv_1 / 2.0)
        if tmp[1] != '0':
            raise ValueError("mean motion 1st derivative too large: " +
                             str(mean_motion_deriv_1))
        l = l + tmp[0] + tmp[2:] # omit the leading zero

        def tle_weirdo_float(val):
            #7 characters, 'smmmmm-e' = 0.mmmmm * 10^-e
            if abs(val) < 1E-14:
                return " 00000-0"
            f = '-' if (val < 0) else ' '
            tmp = "%.4E" % abs(val)
            return f + tmp[0] + tmp[2:6] + "%+2d" % (int(tmp[7:]) + 1)

        l = l + " " + tle_weirdo_float(self.mean_motion_deriv_2 / 6.0)
        l = l + " " + tle_weirdo_float(self.bstar) + " 0 %4d" % self.el_set_no
        if len(l) != 68:
            raise ValueError("line1(): len('%s') != 68" % l)
        return l + _linesum(l)


    def line2(self):
        l = "2 %05d %08.4f %08.4f " % (self.sat_no, self.inclination, self.raan)
        l = l + ("%.7f" % self.ecc)[2:] + " "
        l = l + "%08.4f %08.4f %011.8f" % (self.arg_pe, self.mean_anom, self.mean_motion)
        l = l + "%5d" % self.rev_no
        if len(l) != 68:
            raise ValueError("line2(): len('%s') != 68" % l)
        return l + _linesum(l)

    def epoch_unixtime(self):
        epoch = calendar.timegm(time.strptime(
            "%d %d UTC" % (self.epoch_year, int(self.epoch_jday)),
            "%Y %j %Z"))
        epoch += (self.epoch_jday - int(self.epoch_jday)) * 86400
        return epoch

    def __repr__(self):
        return "\n".join(["0 " + self.sat_name, self.line1(), self.line2()])

def load_catalog(filename, ignore_checksum=False):
    fin = open(filename,'r')
    lines=["","",""]
    i = 0
    tles={}
    for line in fin:
        lines[i] = line.rstrip()
        i = (i + 1) % 3
        if (i == 0):
            tle = TLE(lines, ignore_checksum)
            tles[tle.sat_no] = tle

    fin.close()
    return tles

def load_seq(filename, ignore_checksum=False):
    fin = open(filename,'r')
    lines=["","",""]
    i = 0
    tles=[]
    for line in fin:
        lines[i] = line.rstrip()
        i = (i + 1) % 3
        if (i == 0):
            tle = TLE(lines, ignore_checksum)
            tles.append(tle)

    fin.close()
    return tles
