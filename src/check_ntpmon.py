#!/usr/bin/python3
#
# Copyright:    (c) 2015-2016 Paul D. Gear
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
from process import ntpchecks


def get_args(checks):
    parser = argparse.ArgumentParser(description='NTPmon - Nagios check')
    parser.add_argument(
        '--check',
        choices=checks,
        nargs='*',
        help='Select checks to run; if omitted, run all checks except trace.')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Include command output and internal state dump along with check results.')
    parser.add_argument(
        '--run-time',
        default=512,
        type=int,
        help='Time in seconds (default: 512) for which to always return OK after NTP daemon startup.')
    parser.add_argument(
        '--test',
        action='store_true',
        help='Obtain peer stats on standard input instead of from running daemon.')
    args = parser.parse_args()
    return args


def main():
    validchecks = ['proc', 'offset', 'peers', 'reach', 'sync', 'trace', 'vars']
    defaultchecks = ['proc', 'offset', 'peers', 'reach', 'sync', 'vars']
    args = get_args(validchecks)
    if args.check is None or len(args.check) < 1:
        args.check = defaultchecks

    if args.test:
        # read from standard input in test mode
        checkobjs = {
            'peers': NTPPeers([x.rstrip() for x in sys.stdin.readlines()]),
        }
    else:
        # run the checks
        checkobjs = ntpchecks(args.check, debug=args.debug)

    # alert on what we've collected
    alerter = NTPAlerter(args.check)
    alerter.alert_nagios(checkobjs=checkobjs, debug=args.debug)
    sys.exit(alerter.return_code())


if __name__ == '__main__':
    main()
