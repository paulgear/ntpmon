#!/usr/bin/python3
#
# Copyright:    (c) 2016, 2019 Paul D. Gear
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

import alert
import process


def get_args():
    parser = argparse.ArgumentParser(description='NTPmon - NTP metrics monitor')
    parser.add_argument(
        '--mode',
        type=str,
        choices=[
            'collectd',
            'prometheus',
            'telegraf',
        ],
        help='Collectd is the default if collectd environment variables are detected.',
    )
    parser.add_argument(
        '--connect',
        type=str,
        help='Connect string (in host:port format) to use when sending data to telegraf (default: 127.0.0.1:8094)',
        default='127.0.0.1:8094',
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='How often to report statistics (default: the value of the COLLECTD_INTERVAL environment variable, '
             'or 60 seconds if COLLECTD_INTERVAL is not set).',
    )
    parser.add_argument(
        '--listen-address',
        type=str,
        help='IPv4/IPv6 address on which to listen when acting as a prometheus exporter (default: 127.0.0.1)',
        default='127.0.0.1',
    )
    parser.add_argument(
        '--port',
        type=int,
        help='TCP port on which to listen when acting as a prometheus exporter (default: 9648)',
        default=9648,
    )
    args = parser.parse_args()
    return args


def sleep_until(interval):
    """
    sleep until the end of the interval
    """
    now = time.time()
    s = interval - now % interval
    if sys.stdout.isatty():
        print('Sleeping %g seconds' % (s,))
    time.sleep(s)
    if sys.stdout.isatty():
        print(time.asctime())


def main():
    checks = ['proc', 'offset', 'peers', 'reach', 'sync', 'vars']
    args = get_args()

    if 'COLLECTD_HOSTNAME' in os.environ:
        args.mode = 'collectd'
        hostname = os.environ['COLLECTD_HOSTNAME']
    else:
        hostname = socket.getfqdn()

    if 'COLLECTD_INTERVAL' in os.environ:
        args.mode = 'collectd'
        if args.interval is None:
            args.interval = float(os.environ['COLLECTD_INTERVAL'])

    if args.interval is None:
        args.interval = 60

    debug = sys.stdout.isatty()
    if not debug:
        if args.mode == 'telegraf':
            (host, port) = args.connect.split(':')
            port = int(port)
            s = socket.socket()
            s.connect((host, port))
            sys.stdout = s.makefile(mode='w')
        elif args.mode == 'prometheus':
            import prometheus_client
            prometheus_client.start_http_server(addr=args.listen_address, port=args.port)

    alerter = alert.NTPAlerter(checks)
    implementation = None
    while True:
        # cache implementation for the lifetime of ntpmon
        if not implementation:
            implementation = process.detect_implementation()

        if implementation:
            # run the checks
            checkobjs = process.ntpchecks(checks, debug=False, implementation=implementation)
            # alert on what we've collected
            alerter.alert(checkobjs=checkobjs, hostname=hostname, interval=args.interval, format=args.mode, debug=debug)

        sleep_until(args.interval)


if __name__ == '__main__':
    main()
