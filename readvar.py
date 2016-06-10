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

"""
Parse 'ntpq -nc readvar' output and extract metrics.
"""


class NTPVars(object):

    def __init__(self, lines=None):
        if not isinstance(lines, str):
            # multiple lines - join them
            lines = " ".join(lines)

        # single string - split it by commas, remove whitespace
        rv = [v.strip() for v in lines.split(',')]

        # split each string into metric name + value
        self.metrics = {}
        for v in rv:
            nameval = v.split('=')
            if len(nameval) == 2:
                try:
                    if nameval[0] in ['rootdelay', 'rootdisp', 'sysoffset']:
                        # convert from milliseconds to seconds
                        self.metrics[nameval[0]] = round(float(nameval[1]) / 1000.0, 6)
                    else:
                        self.metrics[nameval[0]] = float(nameval[1])
                except ValueError:
                    # ignore non-numeric values
                    pass

    def getmetrics(self):
        return self.metrics


if __name__ == "__main__":
    import pprint
    import process
    nv = NTPVars(process.execute('vars'))
    v = nv.getmetrics()
    pprint.pprint(v)
