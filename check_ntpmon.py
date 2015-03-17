#!/usr/bin/python
#
# Author:       Paul Gear
# Copyright:	(c) 2015 Gear Consulting Pty Ltd <http://libertysys.com.au/>
# License:	GPLv3 <http://www.gnu.org/licenses/gpl.html>
# Description:  NTP metrics as defined by ntpmon as a Nagios check.
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

import re


def ishostnamey(name):
    """Return true if the passed name is roughly hostnamey.  NTP is casual about how it reports
    hostnames and IP addresses, so we can't be too strict.  This function simply tests that all of
    the characters in the string are letters, digits, dash, or period."""
    return re.search(r'^[\w.-]*$', name) is not None and name.find('_') == -1


def isipaddressy(name):
    """Return true if the passed name is roughly ip addressy.  NTP is very 'casual' about how it
    reports hostnames and IP addresses, so we can't be too strict.  This function simply tests
    that all of the characters in the string are hexadecimal digits, period, or colon."""
    return re.search(r'^[0-9a-f.:]*$', name) is not None


class CheckNTPMon(object):

    okpeers = 0
    warnpeers = 0
    critoffset = 0
    warnoffset = 0
    critreach = 0
    warnreach = 0

    def __init__(self, warnpeers=2, okpeers=4, warnoffset=10, critoffset=50, warnreach=75,
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
            print "OK: %d functional peers" % n
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
            print "CRITICAL: Offset too high (%g) - must be less than %g" % (offset,
                    self.critoffset)
            return 2
        if abs(offset) > self.warnoffset:
            print "WARNING: Offset too high (%g) - should be less than %g" % (offset,
                    self.warnoffset)
            return 1
        else:
            print "OK: Offset normal (%d)" % (offset)
            return 0

    def reachability(self, percent):
        """Return 0 if the reachability percentage is OK
        Return 1 if the reachability percentage is warning
        Return 2 if the reachability percentage is critical
        Raise a ValueError if reachability is not a percentage"""
        if percent < 0 or percent > 100:
            raise ValueError('Value must be a percentage')
        if percent <= self.critreach:
            print "CRITICAL: Reachability too low (%g) - must be more than %g" % (percent,
                    self.critreach)
            return 2
        elif percent <= self.warnreach:
            print "WARNING: Reachability too low (%g) - should be more than %g" % (percent,
                    self.warnreach)
            return 1
        else:
            print "OK: Reachability normal (%g)" % (percent)
            return 0

    def sync(self, synchost):
        """Return true if the synchost is non-zero in length and is a roughly valid host identifier"""
        return len(synchost) > 0 and (ishostnamey(synchost) or isipaddressy(synchost))


#class NTPData(object):
#
#    def __init__(self, peerlines):
#        pass
#

def main():
    # parse args
    # call ntpq -pn
    # parse ntpq output
    # check results
    # return correct error code
    pass


if __name__ == "__main__":
    main()

