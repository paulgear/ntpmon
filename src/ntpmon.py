#!/usr/bin/env python3
#
# Copyright:    (c) 2016-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import argparse
import asyncio
import os
import socket
import sys
import time

import alert
import outputs
import peer_stats
import process
import version

from tailer import Tailer


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NTPmon - NTP metrics monitor")
    parser.add_argument(
        "--mode",
        type=str,
        choices=[
            "collectd",
            "prometheus",
            "telegraf",
        ],
        help="Collectd is the default if collectd environment variables are detected.",
    )
    parser.add_argument(
        "--connect",
        type=str,
        help="Connect string (in host:port format) to use when sending data to telegraf (default: 127.0.0.1:8094)",
        default="127.0.0.1:8094",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode (default: True if standard output is a tty device)",
        default=sys.stdout.isatty(),
    )
    parser.add_argument(
        "--hostname",
        type=str,
        help="The hostname to use for sending collectd metrics",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="How often to report statistics (default: the value of the COLLECTD_INTERVAL environment variable, "
        "or 60 seconds if COLLECTD_INTERVAL is not set).",
    )
    parser.add_argument(
        "--listen-address",
        type=str,
        help="IPv4/IPv6 address on which to listen when acting as a prometheus exporter (default: 127.0.0.1)",
        default="127.0.0.1",
    )
    parser.add_argument(
        "--logfile",
        type=str,
        help="Log file to follow for peer statistics, if different from the default",
    )
    parser.add_argument(
        "--no-debug",
        action="store_false",
        dest="debug",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="TCP port on which to listen when acting as a prometheus exporter (default: 9648)",
        default=9648,
    )
    parser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Print the ntpmon version and exit",
    )
    args = parser.parse_args()

    if args.version:
        print(version.get_version())
        sys.exit(0)

    if "COLLECTD_INTERVAL" in os.environ:
        if args.interval is None:
            args.interval = float(os.environ["COLLECTD_INTERVAL"])
        if args.mode is None:
            args.mode = "collectd"

    if "COLLECTD_HOSTNAME" in os.environ:
        if args.hostname is None:
            args.hostname = os.environ["COLLECTD_HOSTNAME"]
        if args.mode is None:
            args.mode = "collectd"

    if args.hostname is None:
        args.hostname = socket.getfqdn()

    if args.interval is None:
        args.interval = 60

    return args


def get_time_until(interval: int) -> float:
    now = time.time()
    return interval - now % interval


checkobjs = None


def find_type(source: str, peerobjs: dict) -> str:
    """Return the type of the given source based on the data already collected in peerobjs."""
    # the order of these is significant, because pps is included in sync, and sync is included in survivor
    try:
        for type in ["pps", "sync", "invalid", "false", "excess", "backup", "outlier", "survivor", "unknown"]:
            if type not in peerobjs:
                continue
            if source in peerobjs[type]["address"]:
                return type
    except Exception:
        return "UNKNOWN"


async def peer_stats_task(args: argparse.Namespace, output: outputs.Output) -> None:
    """Tail the peer stats log file and send the measurements to the selected output"""
    global checkobjs
    implementation = None
    logfile = args.logfile
    tailer = None

    while True:
        await asyncio.sleep(3)

        if implementation is None:
            implementation = process.get_implementation()
        if implementation is None:
            continue

        if logfile is None:
            logfile = process.get_logfile(implementation)
        if logfile is None:
            continue

        if tailer is None:
            tailer = Tailer(logfile)
        if tailer is None:
            continue

        lines = tailer.tail()
        if lines is None:
            continue

        for line in lines:
            stats = peer_stats.parse_measurement(line)
            if stats is not None:
                if "peertype" not in stats:
                    stats["peertype"] = find_type(stats["source"], checkobjs["peers"].peers)
                output.send_measurement(stats, debug=args.debug)


async def summary_stats_task(args: argparse.Namespace, output: outputs.Output) -> None:
    global checkobjs
    checks = ["proc", "offset", "peers", "reach", "sync", "vars"]
    alerter = alert.NTPAlerter(checks)
    while True:
        implementation = process.get_implementation()
        if implementation:
            # run the checks, returning their data
            checkobjs = process.ntpchecks(checks, debug=False, implementation=implementation)
            # alert on the data collected
            alerter.alert(checkobjs=checkobjs, output=output, debug=args.debug)

        await asyncio.sleep(get_time_until(args.interval))


async def start_tasks(args: argparse.Namespace) -> None:
    output = outputs.get_output(args)
    peer_stats = asyncio.create_task(peer_stats_task(args, output), name="peerstats")
    summary_stats = asyncio.create_task(summary_stats_task(args, output), name="summarystats")
    await asyncio.wait((peer_stats, summary_stats), return_when=asyncio.FIRST_COMPLETED)


if __name__ == "__main__":
    asyncio.run(start_tasks(get_args()))
