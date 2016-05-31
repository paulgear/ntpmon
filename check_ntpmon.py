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

import argparse
import sys

from alert import NTPAlerter
from peers import NTPPeers
from process import ntpchecks, NTPProcess


def get_args(checks):
    parser = argparse.ArgumentParser(description='NTPmon - Nagios check')
    parser.add_argument(
        '--check',
        action='append',
        choices=checks,
        help='Select check(s) to run; if omitted, run all checks.')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Include command output and internal state dump along with check results.')
    parser.add_argument(
        '--run-time',
        default=512,
        type=int,
        help='Time in seconds (default: 512) for which to always return OK after ntpd startup.')
    parser.add_argument(
        '--test',
        action='store_true',
        help='Accept "ntpq -pn" output on standard input instead of running it.')
    args = parser.parse_args()
    return args


def main():
    checks = ['offset', 'peers', 'reach', 'sync', 'trace']
    args = get_args(checks)
    if args.check is None or len(args.check) < 1:
        args.check = checks

    if args.test:
        # read in ntpq output in test mode
        ntppeers = NTPPeers([x.rstrip() for x in sys.stdin.readlines()])
        ntptrace = None
        ntpproc = None
    else:
        # Don't report anything other than OK until ntpd has been running for at
        # least enough time for 8 polling intervals of 64 seconds each.  This
        # prevents false positives due to ntpd restarts or short-lived VMs.
        ntpproc = NTPProcess()
        runtime = ntpproc.check_runtime(args.run_time, debug=args.debug)
        if runtime == 0:
            sys.exit(0)
        elif runtime < 0:
            sys.exit(2)

        # run the checks
        (ntppeers, ntptrace) = ntpchecks(args.check, args.debug)

    # alert on what we've collected
    alerter = NTPAlerter(args.check, ntppeers, ntptrace, ntpproc)
    alerter.alert(args.debug)
    sys.exit(alerter.return_code())


if __name__ == "__main__":
    main()

