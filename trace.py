#!/usr/bin/env python3
#
# Copyright:    (c) 2016 Paul D. Gear
# License:      GPLv3 <http://www.gnu.org/licenses/gpl.html>
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

import ipaddress


def get_hosts(lines):
    """
    Yield the list of hosts from the output of an NTP trace.
    """
    for l in lines:
        line = l.split()
        if len(line) <= 0:
            continue
        host = line[0]
        if not host[-2:] == "::":
            host = host.rstrip(":")
        try:
            ip = ipaddress.ip_address(host)
            yield str(ip)
        except ValueError:
            pass


class NTPTrace(object):

    def trace(self, lines):
        results = {
            'tracehosts': 0,
            'tracerepeats': 0,
        }
        seen = set()
        self.loophost = None
        self.hostlist = []
        for h in get_hosts(lines):
            if h in seen:
                if self.loophost is None:
                    self.loophost = h
                results['tracerepeats'] += 1
            else:
                self.hostlist.append(h)
            seen.add(h)
            results['tracehosts'] += 1
        self.results = results
        return results

    def __init__(self, lines):
        self.trace(lines)

    def getmetrics(self):
        return self.results.copy()


def main():
    pass

if __name__ == "__main__":
    main()
