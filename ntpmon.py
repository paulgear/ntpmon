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
import os
import socket
import sys
import time
import warnings

from alert import NTPAlerter
from process import ntpchecks


def get_args():
    parser = argparse.ArgumentParser(description='NTPmon - NTP metrics monitor')
    parser.add_argument(
        '--mode',
        type=str,
        help='Collectd is the default if collectd environment variables are detected.')
    parser.add_argument(
        '--interval',
        type=int,
        help='How often to report statistics (default: the value of the COLLECTD_INTERVAL environment variable, or 60 seconds if COLLECTD_INTERVAL is not set).')
    args = parser.parse_args()
    return args


def sleep_until(interval):
    """
    FIXME: only sleep until the end of the interval
    """
    time.sleep(interval)


def main():
    checks = ['proc', 'offset', 'peers', 'reach', 'sync', 'vars', 'trace']
    args = get_args()

    if 'COLLECTD_HOSTNAME' in os.environ:
        args.mode = 'collectd'
        hostname = os.environ['COLLECTD_HOSTNAME']
    else:
        hostname = socket.getfqdn()

    if 'COLLECTD_INTERVAL' in os.environ:
        args.mode = 'collectd'
        if args.interval is None:
            args.interval = int(os.environ['COLLECTD_INTERVAL'])

    if args.interval is None:
        args.interval = 60

    if args.mode != 'collectd':
        warnings.warn('Only collectd mode is currently supported')
        sys.exit(1)

    while True:
        # run the checks
        checkobjs = ntpchecks(checks, debug=False)

        # alert on what we've collected
        alerter = NTPAlerter(checks, checkobjs)
        alerter.alert_collectd(hostname, args.interval)
        sleep_until(args.interval)


if __name__ == "__main__":
    main()

