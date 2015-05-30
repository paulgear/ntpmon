#!/usr/bin/python
#
# Author:       Paul Gear
# Copyright:    (c) 2015 Gear Consulting Pty Ltd <http://libertysys.com.au/>
# License:      GPLv3 <http://www.gnu.org/licenses/gpl.html>
# Description:  NTP metrics as a Nagios check.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import psutil
import re
import subprocess
import sys
import time
import traceback
import warnings


def ishostnamey(name):
    """Return true if the passed name is roughly hostnamey.  NTP is rather casual about how it
    reports hostnames and IP addresses, so we can't be too strict.  This method simply tests
    that all of the characters in the string are letters, digits, dash, or period."""
    return re.search(r'^[\w.-]*$', name) is not None and name.find('_') == -1


def isipaddressy(name):
    """Return true if the passed name is roughly IP addressy.  NTP is rather casual about how it
    reports hostnames and IP addresses, so we can't be too strict.  This method simply tests
    that all of the characters in the string are hexadecimal digits, period, or colon."""
    return re.search(r'^[0-9a-f.:]*$', name) is not None


class CheckNTPMonSilent(object):

    def __init__(self,
                 warnpeers=2,
                 okpeers=4,
                 warnoffset=10,
                 critoffset=50,
                 warnreach=75,
                 critreach=50):
        self.warnpeers = warnpeers
        self.okpeers = okpeers
        self.warnoffset = warnoffset
        self.critoffset = critoffset
        self.warnreach = warnreach
        self.critreach = critreach

    def peers(self, n):
        if n >= self.okpeers:
            return (0, "OK: %d usable peers" % (n))
        elif n < self.warnpeers:
            return (2, "CRITICAL: Too few peers (%d) - must be at least %d" %
                    (n, self.warnpeers))
        else:
            return (1, "WARNING: Too few peers (%d) - should be at least %d" %
                    (n, self.okpeers))

    def offset(self, offset):
        if abs(offset) > self.critoffset:
            return (2,
                    "CRITICAL: Offset too high (%g) - must be less than %g" %
                    (offset, self.critoffset))
        if abs(offset) > self.warnoffset:
            return (1,
                    "WARNING: Offset too high (%g) - should be less than %g" %
                    (offset, self.warnoffset))
        else:
            return (0, "OK: Offset normal (%g)" % (offset))

    def reachability(self, percent):
        if percent < 0 or percent > 100:
            raise ValueError('Value must be a percentage')
        if percent <= self.critreach:
            return (
                2,
                "CRITICAL: Reachability too low (%g%%) - must be more than %g%%" %
                (percent, self.critreach))
        elif percent <= self.warnreach:
            return (
                1,
                "WARNING: Reachability too low (%g%%) - should be more than %g%%" %
                (percent, self.warnreach))
        else:
            return (0, "OK: Reachability normal (%g%%)" % (percent))

    def sync(self, synchost):
        synced = len(synchost) > 0 and (ishostnamey(synchost) or
                                        isipaddressy(synchost))
        if synced:
            return (0, "OK: time is in sync with %s" % (synchost))
        else:
            return (2, "CRITICAL: no sync host selected")

    def is_silent(self):
        return True

    def dump(self):
        print "warnpeers  = %d" % (self.warnpeers)
        print "okpeers    = %d" % (self.okpeers)
        print "warnoffset = %g" % (self.warnoffset)
        print "critoffset = %g" % (self.critoffset)
        print "warnreach  = %g" % (self.warnreach)
        print "critreach  = %g" % (self.critreach)

    @classmethod
    def clone(cls, obj):
        # must actually be a CheckNTPMonSilent object
        assert obj.warnpeers is not None
        if obj.is_silent():
            return obj
        else:
            return CheckNTPMonSilent(warnpeers=obj.warnpeers,
                                     okpeers=obj.okpeers,
                                     warnoffset=obj.warnoffset,
                                     critoffset=obj.critoffset,
                                     warnreach=obj.warnreach,
                                     critreach=obj.critreach)


class CheckNTPMon(CheckNTPMonSilent):

    """Version of CheckNTPMonSilent which prints out the diagnostic message and returns
    integer return code instead of a list"""

    def __init__(self,
                 warnpeers=2,
                 okpeers=4,
                 warnoffset=10,
                 critoffset=50,
                 warnreach=75,
                 critreach=50):
        CheckNTPMonSilent.__init__(self, warnpeers, okpeers, warnoffset,
                                   critoffset, warnreach, critreach)

    def peers(self, n):
        """Return 0 if the number of peers is OK
        Return 1 if the number of peers is WARNING
        Return 2 if the number of peers is CRITICAL"""
        code, msg = CheckNTPMonSilent.peers(self, n)
        print msg
        return code

    def offset(self, offset):
        """Return 0 if the offset is OK
        Return 1 if the offset is WARNING
        Return 2 if the offset is CRITICAL"""
        code, msg = CheckNTPMonSilent.offset(self, offset)
        print msg
        return code

    def reachability(self, percent):
        """Return 0 if the reachability percentage is OK
        Return 1 if the reachability percentage is warning
        Return 2 if the reachability percentage is critical
        Raise a ValueError if reachability is not a percentage"""
        code, msg = CheckNTPMonSilent.reachability(self, percent)
        print msg
        return code

    def sync(self, synchost):
        """Return 0 if the synchost is non-zero in length and is a roughly valid host identifier
        Return 2 otherwise"""
        code, msg = CheckNTPMonSilent.sync(self, synchost)
        print msg
        return code

    def is_silent(self):
        return False


class NTPPeers(object):

    """Turn the peer lines returned by 'ntpq -pn' into a data structure usable for checks."""

    noiselines = [
        r'remote\s+refid\s+st\s+t\s+when\s+poll\s+reach\s+',
        r'^=*$',
        r'No association ID.s returned',
    ]
    ignorepeers = [".LOCL.", ".INIT.", ".XFAC."]

    def isnoiseline(self, line):
        for regex in self.noiselines:
            if re.search(regex, line) is not None:
                return True
        return False

    def shouldignore(self, fields, l):
        if len(fields) != 10:
            warnings.warn('Invalid ntpq peer line - there are %d fields: %s' %
                          (len(fields), l))
            return True
        if fields[1] in self.ignorepeers:
            return True
        if int(fields[2]) > 15:
            return True
        return False

    def parsetally(self, tally, peerdata, offset):
        """Parse the tally code and add the appropriate items to the peer data based on that code.
           See the explanation of tally codes in the ntpq documentation for how these work:
             - http://www.eecis.udel.edu/~mills/ntp/html/decode.html#peer
             - http://www.eecis.udel.edu/~mills/ntp/html/ntpq.html
             - http://psp2.ntp.org/bin/view/Support/TroubleshootingNTP
        """
        if tally in ['*', 'o'] and 'syncpeer' not in self.ntpdata:
            # this is our sync peer
            self.ntpdata['syncpeer'] = peerdata['peer']
            self.ntpdata['offsetsyncpeer'] = offset
            self.ntpdata['survivors'] += 1
            self.ntpdata['offsetsurvivors'] += offset
        elif tally in ['+', '#']:
            # valid peer
            self.ntpdata['survivors'] += 1
            self.ntpdata['offsetsurvivors'] += offset
        elif tally in [' ', 'x', '.', '-']:
            # discarded peer
            self.ntpdata['discards'] += 1
            self.ntpdata['offsetdiscards'] += offset
        else:
            self.ntpdata['unknown'] += 1
            return False
        return True

    def __init__(self, peerlines, check=None):
        self.ntpdata = {
            'survivors': 0,
            'offsetsurvivors': 0,
            'discards': 0,
            'offsetdiscards': 0,
            'unknown': 0,
            'peers': 0,
            'offsetall': 0,
            'totalreach': 0,
        }
        self.check = check

        for l in peerlines:
            if self.isnoiseline(l):
                continue

            # first column is the tally field, the rest are
            # whitespace-separated fields
            tally = l[0]
            fields = l[1:-1].split()

            if self.shouldignore(fields, l):
                continue

            fieldnames = ['peer', 'refid', 'stratum', 'type', 'lastpoll',
                          'interval', 'reach', 'delay', 'offset', 'jitter']
            peerdata = dict(zip(fieldnames, fields))

            offset = abs(float(peerdata['offset']))
            if not self.parsetally(tally, peerdata, offset):
                warnings.warn(
                    'Unknown tally code detected - please report a bug: %s' %
                    (l))
                continue

            self.ntpdata['peers'] += 1
            self.ntpdata['offsetall'] += offset

            # reachability - this counts the number of bits set in the reachability field
            # (which is displayed in octal in the ntpq output)
            # http://stackoverflow.com/questions/9829578/fast-way-of-counting-bits-in-python
            self.ntpdata['totalreach'] += bin(int(peerdata['reach'],
                                                  8)).count("1")

        # average offsets
        if self.ntpdata['survivors'] > 0:
            self.ntpdata['averageoffsetsurvivors'] = self.ntpdata['offsetsurvivors'] / self.ntpdata['survivors']
        if self.ntpdata['discards'] > 0:
            self.ntpdata['averageoffsetdiscards'] = self.ntpdata['offsetdiscards'] / self.ntpdata['discards']

        if self.ntpdata['peers'] > 0:
            # precent average reachability of all peers over the last 8 polls
            reach = float(self.ntpdata['totalreach']) * 100 / self.ntpdata['peers']
            self.ntpdata['reachability'] = reach / 8

            # average offset of all peers
            self.ntpdata['averageoffset'] = self.ntpdata['offsetall'] / self.ntpdata['peers']
        else:
            # if there are no peers, reachability is zero and average offset is invalid
            self.ntpdata['reachability'] = 0.0
            self.ntpdata['averageoffset'] = float('nan')

    def dump(self):
        if self.ntpdata.get('syncpeer'):
            print "Synced to: %s, offset %g ms" % (
                self.ntpdata['syncpeer'], self.ntpdata['offsetsyncpeer'])
        else:
            print "No remote sync peer"
        print "%d total peers, average offset %g ms" % (
            self.ntpdata['peers'], self.ntpdata['averageoffset'])
        if self.ntpdata['survivors'] > 0:
            print "%d good peers, average offset %g ms" % (
                self.ntpdata['survivors'], self.ntpdata['averageoffsetsurvivors'])
        if self.ntpdata['discards'] > 0:
            print "%d discarded peers, average offset %g ms" % (
                self.ntpdata['discards'], self.ntpdata['averageoffsetdiscards'])
        print "Average reachability of all peers: %d%%" % (
            self.ntpdata['reachability'])

    def check_peers(self, check=None):
        """Check the number of usable peers"""
        if check is None:
            check = self.check if self.check else CheckNTPMon()
        return check.peers(self.ntpdata['peers'])

    def check_offset(self, check=None):
        """Check the offset from the sync peer, returning critical, warning,
            or OK based on the CheckNTPMon results.
        If there is no sync peer, use the average offset of survivors instead.
        If there are no survivors, use the average offset of discards instead,
            and return warning as a minimum.
        If there are no discards, return critical.
        """
        result = 0
        if check is None:
            check = self.check if self.check else CheckNTPMon()
        if 'offsetsyncpeer' in self.ntpdata:
            return check.offset(self.ntpdata['offsetsyncpeer'])
        if 'averageoffsetsurvivors' in self.ntpdata:
            return check.offset(self.ntpdata['averageoffsetsurvivors'])
        if 'averageoffsetdiscards' in self.ntpdata:
            result = check.offset(self.ntpdata['averageoffsetdiscards'])
            msg = "WARNING: No sync peer or survivors - used discard offsets"
            if check.is_silent():
                return [1 if result[0] < 1 else result[0],
                          msg + " (" + result[1] + ")"]
            else:
                print msg
                return 1 if result < 1 else result
        else:
            ret = [2, "CRITICAL: No peers for which to check offset"]
            if check.is_silent():
                return ret
            else:
                print ret[1]
                return ret[0]

    def check_reachability(self, check=None):
        """Check reachability of all peers"""
        if check is None:
            check = self.check if self.check else CheckNTPMon()
        return check.reachability(self.ntpdata['reachability'])

    def check_sync(self, check=None):
        """Check whether host is in sync with a peer"""
        if check is None:
            check = self.check if self.check else CheckNTPMon()
        if self.ntpdata.get('syncpeer') is None:
            ret = [2, "CRITICAL: No sync peer"]
            if check.is_silent():
                return ret
            else:
                print ret[1]
                return ret[0]
        return check.sync(self.ntpdata['syncpeer'])

    def checks(self, methods=None, check=None):
        """Run the specified list of checks (or all of them if none is supplied)
        and return the worst result.  Output only the diagnostic message for that
        result."""

        # ensure check exists and is silent
        if check is None:
            check = self.check if self.check else CheckNTPMonSilent()
        if not check.is_silent():
            check = CheckNTPMonSilent.clone(check)
        assert check.is_silent()

        if not methods:
            methods = [self.check_offset, self.check_peers,
                       self.check_reachability, self.check_sync]

        ret = -1
        msg = None
        for method in methods:
            result = method(check=check)
            if ret < result[0]:
                ret = result[0]
                msg = result[1]

        if msg is None:
            print "%s returned no results - please report a bug" % (method)
            return 3
        print msg
        return ret

    @staticmethod
    def query():
        lines = None
        try:
            null = open("/dev/null", "a")
            output = subprocess.check_output(["ntpq", "-pn"], stderr=null)
            if len(output) > 0:
                lines = output.split("\n")
        except:
            traceback.print_exc(file=sys.stdout)
        return lines


class NTPProcess(object):

    def __init__(self, names=None):
        """Look for ntpd or xntpd in the process table and save its process object."""
        if names is None:
            names = ["ntpd", "xntpd"]
        # Check for old psutil per http://grodola.blogspot.com.au/2014/01/psutil-20-porting.html
        self.PSUTIL2 = psutil.version_info >= (2, 0)
        self.proc = None
        for proc in psutil.process_iter():
            try:
                name = proc.name() if self.PSUTIL2 else proc.name
                if name in names:
                    self.proc = proc
                    break
            except psutil.Error:
                pass

    def runtime(self):
        """Return the length of time in seconds that the process has been running.
        If ntpd is not running or any error occurs, return -1."""
        if self.proc is None:
            return -1
        try:
            now = time.time()
            create_time = self.proc.create_time() if self.PSUTIL2 else self.proc.create_time
            start = int(create_time)
            return now - start
        except psutil.Error:
            return -1


def main():
    methodnames = ['offset', 'peers', 'reachability', 'sync']
    options = {
        'warnpeers': [
            2, int, 'Minimum number of peers to be considered non-critical',
        ],
        'okpeers': [
            4, int, 'Minimum number of peers to be considered OK',
        ],
        'warnoffset': [
            10, float, 'Minimum offset to be considered warning',
        ],
        'critoffset': [
            50, float, 'Minimum offset to be considered critical',
        ],
        'warnreach': [
            75, float, 'Minimum peer reachability percentage to be considered OK',
        ],
        'critreach': [
            50, float, 'Minimum peer reachability percentage to be considered non-crtical',
        ],
    }

    # Create check ranges; will be used by parse_args to store options
    checkntpmon = CheckNTPMon()

    # parse command line
    parser = argparse.ArgumentParser(
        description='Nagios NTP check incorporating the logic of NTPmon')
    parser.add_argument(
        '--check',
        choices=methodnames,
        help='Select check to run; if omitted, run all checks and return the worst result.')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Include "ntpq -pn" output and internal state dump along with check results.')
    parser.add_argument(
        '--run-time',
        default=512,
        type=int,
        help='Time in seconds (default: 512) for which to always return OK after ntpd startup.')
    parser.add_argument(
        '--test',
        action='store_true',
        help='Accept "ntpq -pn" output on standard input instead of running it.')
    for o in options.keys():
        helptext = options[o][2] + ' (default: %d)' % (options[o][0])
        parser.add_argument('--' + o,
                            default=options[o][0],
                            help=helptext,
                            type=options[o][1])
    args = parser.parse_args(namespace=checkntpmon)

    # run ntpq
    lines = NTPPeers.query() if not args.test else [x.rstrip() for x in sys.stdin.readlines()]
    if lines is None:
        # Unknown result
        print "UNKNOWN: Cannot get peers from ntpq.  Please check that an NTP server is installed and running."
        sys.exit(3)

    # Don't report anything other than OK until ntpd has been running for at
    # least enough time for 8 polling intervals of 64 seconds each.
    age = NTPProcess().runtime()
    if age > 0 and age <= args.run_time:
        print "OK: ntpd still starting up (running %d seconds)" % age
        sys.exit(0)

    # initialise our object with the results of ntpq and our preferred check
    # thresholds
    ntp = NTPPeers(lines, checkntpmon)

    if args.debug:
        print "\n".join(lines)
        checkntpmon.dump()
        ntp.dump()

    # work out which method to run
    # (methods must be in the same order as methodnames above)
    methods = [ntp.check_offset, ntp.check_peers, ntp.check_reachability,
               ntp.check_sync]
    checkmethods = dict(zip(methodnames, methods))

    # if check argument is specified, run just that check
    ret = 0
    if checkmethods.get(args.check):
        method = checkmethods[args.check]
        ret = method()
    # else check all the methods
    else:
        ret = ntp.checks()

    sys.exit(ret)


if __name__ == "__main__":
    main()
