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
import re
import subprocess
import sys
import traceback
import warnings


def ishostnamey(name):
    """Return true if the passed name is roughly hostnamey.  NTP is rather casual about how it
    reports hostnames and IP addresses, so we can't be too strict.  This function simply tests
    that all of the characters in the string are letters, digits, dash, or period."""
    return re.search(r'^[\w.-]*$', name) is not None and name.find('_') == -1


def isipaddressy(name):
    """Return true if the passed name is roughly IP addressy.  NTP is rather casual about how it
    reports hostnames and IP addresses, so we can't be too strict.  This function simply tests
    that all of the characters in the string are hexadecimal digits, period, or colon."""
    return re.search(r'^[0-9a-f.:]*$', name) is not None


class CheckNTPMon(object):

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
        """Return 0 if the number of peers is OK
        Return 1 if the number of peers is WARNING
        Return 2 if the number of peers is CRITICAL"""
        if n >= self.okpeers:
            print "OK: %d configured peers" % n
            return 0
        elif n < self.warnpeers:
            print "CRITICAL: Too few peers (%d) - must be at least %d" % (n, self.warnpeers)
            return 2
        else:
            print "WARNING: Too few peers (%d) - should be at least %d" % (n, self.okpeers)
            return 1

    def offset(self, offset):
        """Return 0 if the offset is OK
        Return 1 if the offset is WARNING
        Return 2 if the offset is CRITICAL"""
        if abs(offset) > self.critoffset:
            print "CRITICAL: Offset too high (%g) - must be less than %g" % \
                    (offset, self.critoffset)
            return 2
        if abs(offset) > self.warnoffset:
            print "WARNING: Offset too high (%g) - should be less than %g" % \
                    (offset, self.warnoffset)
            return 1
        else:
            print "OK: Offset normal (%g)" % (offset)
            return 0

    def reachability(self, percent):
        """Return 0 if the reachability percentage is OK
        Return 1 if the reachability percentage is warning
        Return 2 if the reachability percentage is critical
        Raise a ValueError if reachability is not a percentage"""
        if percent < 0 or percent > 100:
            raise ValueError('Value must be a percentage')
        if percent <= self.critreach:
            print "CRITICAL: Reachability too low (%g%%) - must be more than %g%%" % \
                    (percent, self.critreach)
            return 2
        elif percent <= self.warnreach:
            print "WARNING: Reachability too low (%g%%) - should be more than %g%%" % \
                    (percent, self.warnreach)
            return 1
        else:
            print "OK: Reachability normal (%g)" % (percent)
            return 0

    def sync(self, synchost):
        """Return 0 if the synchost is non-zero in length and is a roughly valid host identifier, return 2 otherwise."""
        synced = len(synchost) > 0 and (ishostnamey(synchost) or isipaddressy(synchost))
        if synced:
            print "OK: time is in sync with %s" % (synchost)
        else:
            print "CRITICAL: no sync host selected"
        return 0 if synced else 2


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
            warnings.warn('Invalid ntpq peer line - there are %d fields: %s' % (len(fields), l))
            return True
        if fields[0] in self.ignorepeers:
            return True
        return False

    def parsetally(self, tally, peerdata):
        """Parse the tally code and add the appropriate items to the peer data based on that code.
           See the explanation of tally codes in the ntpq documentation for how these work:
             - http://www.eecis.udel.edu/~mills/ntp/html/decode.html#peer
             - http://www.eecis.udel.edu/~mills/ntp/html/ntpq.html
             - http://psp2.ntp.org/bin/view/Support/TroubleshootingNTP
        """
        if tally in ['*', 'o'] and 'syncpeer' not in self.ntpdata:
            # this is our sync peer
            self.ntpdata['syncpeer'] = peerdata['peer']
            self.ntpdata['offsetsyncpeer'] = abs(float(peerdata['offset']))
            self.ntpdata['survivors'] += 1
            self.ntpdata['offsetsurvivors'] += abs(float(peerdata['offset']))
        elif tally in ['+', '#']:
            # valid peer
            self.ntpdata['survivors'] += 1
            self.ntpdata['offsetsurvivors'] += abs(float(peerdata['offset']))
        elif tally in [' ', 'x', '.', '-']:
            # discarded peer
            self.ntpdata['discards'] += 1
            self.ntpdata['offsetdiscards'] += abs(float(peerdata['offset']))
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

            # first column is the tally field, the rest are whitespace-separated fields
            tally = l[0]
            fields = l[1:-1].split()

            if self.shouldignore(fields, l):
                continue

            fieldnames = ['peer', 'refid', 'stratum', 'type', 'lastpoll', 'interval', 'reach',
                          'delay', 'offset', 'jitter']
            peerdata = dict(zip(fieldnames, fields))

            if not self.parsetally(tally, peerdata):
                warnings.warn('Unknown tally code detected - please report a bug: %s' % (l))
                continue

            self.ntpdata['peers'] += 1
            self.ntpdata['offsetall'] += abs(float(peerdata['offset']))

            # reachability - this counts the number of bits set in the reachability field
            # (which is displayed in octal in the ntpq output)
            # http://stackoverflow.com/questions/9829578/fast-way-of-counting-bits-in-python
            self.ntpdata['totalreach'] += bin(int(peerdata['reach'], 8)).count("1")

        # reachability as a percentage of the last 8 polls, across all peers
        self.ntpdata['reachability'] = float(self.ntpdata['totalreach']) * 100 / self.ntpdata['peers'] / 8

        # average offsets
        if self.ntpdata['survivors'] > 0:
            self.ntpdata['averageoffsetsurvivors'] = \
                    self.ntpdata['offsetsurvivors'] / self.ntpdata['survivors']
        if self.ntpdata['discards'] > 0:
            self.ntpdata['averageoffsetdiscards'] = \
                    self.ntpdata['offsetdiscards'] / self.ntpdata['discards']
        self.ntpdata['averageoffset'] = self.ntpdata['offsetall'] / self.ntpdata['peers']

    def dump(self):
        if self.ntpdata['syncpeer']:
            print "Synced to: %s, offset %g" % \
                    (self.ntpdata['syncpeer'], self.ntpdata['offsetsyncpeer'])
        print "%d peers, average offset %g" % \
                (self.ntpdata['peers'], self.ntpdata['averageoffset'])
        if self.ntpdata['survivors'] > 0:
            print "%d good peers, average offset %g" % \
                    (self.ntpdata['survivors'], self.ntpdata['averageoffsetsurvivors'])
        if self.ntpdata['discards'] > 0:
            print "%d discarded peers, average offset %g" % \
                    (self.ntpdata['discards'], self.ntpdata['averageoffsetdiscards'])
        print "Average reachability of all peers: %d%%" % (self.ntpdata['reachability'])

    def check_peers(self, check=None):
        """Check the number of configured peers"""
        if check is None:
            check = self.check if self.check else CheckNTPMon()
        return check.peers(self.ntpdata['peers'])

    def check_offset(self, check=None):
        """Check the offset from the sync peer, returning critical, warning,
        or OK based on the CheckNTPMon results.
        If there is no sync peer, use the average offset of survivors instead.
        If there are no survivors, use the average offset of discards instead, and return warning as a minimum.
        If there are no discards, return critical.
        """
        if check is None:
            check = self.check if self.check else CheckNTPMon()
        if 'offsetsyncpeer' in self.ntpdata:
            return check.offset(self.ntpdata['offsetsyncpeer'])
        if 'averageoffsetsurvivors' in self.ntpdata:
            return check.offset(self.ntpdata['averageoffsetsurvivors'])
        if 'averageoffsetdiscards' in self.ntpdata:
            result = check.offset(self.ntpdata['averageoffsetdiscards'])
            return 1 if result < 1 else result
        else:
            print "CRITICAL: No peers for which to check offset"
            return 2

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
            print "CRITICAL: No sync peer"
            return 2
        return check.sync(self.ntpdata['syncpeer'])

    @staticmethod
    def query():
        lines = None
        try:
            output = subprocess.check_output(["ntpq", "-pn"])
            lines = output.split("\n")
        except:
            traceback.print_exc(file=sys.stdout)
        return lines


def main():
    methodnames = ['offset', 'peers', 'reachability', 'sync']
    options = {
        'warnpeers':  [  2, int,   'Minimum number of peers to be considered non-critical'],
        'okpeers':    [  4, int,   'Minimum number of peers to be considered OK'],
        'warnoffset': [ 10, float, 'Minimum offset to be considered warning'],
        'critoffset': [ 50, float, 'Minimum offset to be considered critical'],
        'warnreach':  [ 75, float, 'Minimum peer reachability percentage to be considered OK'],
        'critreach':  [ 50, float, 'Minimum peer reachability percentage to be considered non-crtical'],
    }

    # Create check ranges; will be used by parse_args to store options
    checkntpmon = CheckNTPMon()

    # parse command line
    parser = argparse.ArgumentParser(description='Nagios NTP check incorporating the logic of NTPmon')
    parser.add_argument('--check', choices=methodnames,
            help='Select check to run; if omitted, run all checks and return the worst result.')
    parser.add_argument('--debug', action='store_true',
            help='Include "ntpq -pn" output and internal state dump along with check results.')
    for o in options.keys():
        helptext = options[o][2] + ' (default: %d)' % (options[o][0])
        parser.add_argument('--' + o, default=options[o][0], help=helptext, type=options[o][1])
    args = parser.parse_args(namespace=checkntpmon)

    # run ntpq
    lines = NTPPeers.query()
    if lines is None:
        # Unknown result
        print "Cannot get peers from ntpq."
        print "Please check that an NTP server is installed and functional."
        sys.exit(3)

    # initialise our object with the results of ntpq and our preferred check thresholds
    ntp = NTPPeers(lines, checkntpmon)

    if args.debug:
        print "\n".join(lines)
        ntp.dump()

    # work out which method to run
    # (methods must be in the same order as methodnames above)
    methods = [ntp.check_offset, ntp.check_peers, ntp.check_reachability, ntp.check_sync]
    checkmethods = dict(zip(methodnames, methods))

    # if check argument is specified, run just that check
    ret = 0
    if checkmethods.get(args.check) is not None:
        method = checkmethods[args.check]
        ret = method()
    # else check all the methods
    else:
        for method in methods:
            check = method()
            if ret < check:
                ret = check

    sys.exit(ret)

if __name__ == "__main__":
    main()
