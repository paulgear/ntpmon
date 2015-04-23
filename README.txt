check_ntpmon
by Paul Gear <github@libertysys.com.au>
Copyright (c) 2015 Gear Consulting Pty Ltd <http://libertysys.com.au/>

License
-------

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.


Introduction
------------

check_ntpmon.py is a Nagios check which is designed to report on essential
health metrics for NTP.  It bases its metrics on the same agorithms as those
collected by NTPmon <https://github.com/paulgear/ntpmon>.


Metrics
-------

(TODO)


Startup delay
-------------

(TODO)


Usage
-----

check_ntpmon.py [-h] [--check {offset,peers,reachability,sync}]
                [--debug] [--test] [--critreach CRITREACH]
                [--warnreach WARNREACH] [--okpeers OKPEERS]
                [--warnoffset WARNOFFSET] [--warnpeers WARNPEERS]
                [--critoffset CRITOFFSET]

optional arguments:
  -h, --help            show this help message and exit
  --check {offset,peers,reachability,sync}
                        Select check to run; if omitted, run all checks and
                        return the worst result.
  --debug               Include "ntpq -pn" output and internal state dump
                        along with check results.
  --test                Accept "ntpq -pn" output on standard input instead of
                        running it.
  --critreach CRITREACH
                        Minimum peer reachability percentage to be considered
                        non-crtical (default: 50)
  --warnreach WARNREACH
                        Minimum peer reachability percentage to be considered
                        OK (default: 75)
  --okpeers OKPEERS     Minimum number of peers to be considered OK (default:
                        4)
  --warnoffset WARNOFFSET
                        Minimum offset to be considered warning (default: 10)
  --warnpeers WARNPEERS
                        Minimum number of peers to be considered non-critical
                        (default: 2)
  --critoffset CRITOFFSET
                        Minimum offset to be considered critical (default: 50)


Prerequisites
-------------

check_ntpmon.py is written in python.  It requires modules from the standard
python library, and also requires the psutil library, which is available
from pypi or your operating system repositories.  On Debian and Ubuntu
Linux, psutil can be installed by running:

    apt-get install python-psutil
