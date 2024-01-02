#!/usr/bin/env python3
#
# Copyright:    (c) 2016-2024 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import argparse
import sys

import version

from alert import NTPAlerter
from peers import NTPPeers
from process import ntpchecks


def get_args(checks):
    parser = argparse.ArgumentParser(description="NTPmon - Nagios check")
    parser.add_argument(
        "--check",
        choices=checks,
        nargs="*",
        help="Select checks to run; if omitted, run all checks.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Include command output and internal state dump along with check results.",
    )
    parser.add_argument(
        "--run-time",
        default=512,
        type=int,
        help="Time in seconds (default: 512) for which to always return OK after NTP daemon startup.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Obtain peer stats on standard input instead of from running daemon.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Print the check_ntpmon version and exit",
    )
    args = parser.parse_args()

    if args.version:
        print(version.get_version())
        sys.exit(0)

    return args


def main():
    validchecks = ["proc", "offset", "peers", "reach", "reachability", "sync", "vars"]
    defaultchecks = ["proc", "offset", "peers", "reach", "sync", "vars"]
    args = get_args(validchecks)
    if args.check is None or len(args.check) < 1:
        args.check = defaultchecks
    else:
        # turn 'reachability' into 'reach' for backwards compatibility
        for i in range(0, len(args.check)):
            if args.check[i] == "reachability":
                args.check[i] = "reach"

    if args.test:
        # read from standard input in test mode
        checkobjs = {
            "peers": NTPPeers([x.rstrip() for x in sys.stdin.readlines()]),
        }
    else:
        # run the checks
        checkobjs = ntpchecks(args.check, debug=args.debug)

    # alert on what we've collected
    alerter = NTPAlerter(args.check)
    alerter.alert_nagios(checkobjs=checkobjs, debug=args.debug)
    sys.exit(alerter.return_code())


if __name__ == "__main__":
    main()
