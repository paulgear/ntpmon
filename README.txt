check_ntpmon
by Paul Gear <github@libertysys.com.au>
Copyright (c) 2015-2016 Paul D. Gear <http://libertysys.com.au/>

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

check_ntpmon reports on the following metrics of the local NTP server:

sync:
    Is the clock in sync with one of its peers?  If not, return CRITICAL,
    otherwise return OK.

peers:
    Are there more than the minimum number of peers active?  The NTP
    algorithms require a minimum of 3 peers for accurate clock management; to
    allow for failure or maintenance of one peer at all times, check_ntpmon
    returns OK for 4 or more configured peers, CRITICAL for 1 or 0, and
    WARNING for 2-3.  You can tune these values with --warnpeers and
    --okpeers, but the defaults should suit most sensibly-configured NTP
    servers.

reachability:
    Are the configured peers reliably reachable on the network?  Return
    CRITICAL for less than 50% total reachability of all configured peers;
    return OK for greater than 75% total reachability of all configured peers.
    You can tune these values with --critreach and --warnreach.

offset:
    Is the clock offset from its sync peer acceptable?  Return CRITICAL for
    greater than 50 milliseconds difference, WARNING for greater than 10 ms,
    and OK for anything less.  You can tune these values with --critoffset and
    --warnoffset.

trace:
    Is there a sync loop between the local server and the stratum 1 servers?
    If so, return CRITICAL.  Most public NTP servers do not support tracing,
    so for anything other than a loop (including a timeout), return OK.


Startup delay
-------------

By default, until ntpd has been running for 512 seconds (the minimum time for
8 polls at 64 second intervals), check_ntpmon will return OK (zero return
code).  This is to prevent false positives on startup or for short-lived VMs.


Usage
-----

check_ntpmon.py [-h] [--check {offset,peers,reachability,sync,trace}]
                [--debug] [--test] [--critreach CRITREACH]
                [--warnreach WARNREACH] [--okpeers OKPEERS]
                [--warnoffset WARNOFFSET] [--warnpeers WARNPEERS]
                [--critoffset CRITOFFSET]

optional arguments:
  -h, --help            show this help message and exit
  --check {offset,peers,reachability,sync,trace}
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

check_ntpmon.py also requires 'timeout' from the GNU coreutils distribution,
and 'ntpq' and 'ntptrace' from the NTP distribution.


To do
-----

- Return performance metrics to Nagios for graphing.
