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

from io import TextIOWrapper

import alert
import line_protocol
import peer_stats
import process

from tailer import Tailer


debug = sys.stdout.isatty()


def get_args():
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
        "--port",
        type=int,
        help="TCP port on which to listen when acting as a prometheus exporter (default: 9648)",
        default=9648,
    )
    args = parser.parse_args()
    return args


def get_telegraf_file(connect: str) -> TextIOWrapper:
    """Return a TextIOWrapper for writing data to telegraf"""
    (host, port) = connect.split(":")
    port = int(port)
    s = socket.socket()
    s.connect((host, port))
    return s.makefile(mode="w")


def get_time_until(interval):
    now = time.time()
    return interval - now % interval


checkobjs = None


async def alert_task(args: argparse.Namespace, hostname: str):
    global checkobjs
    checks = ["proc", "offset", "peers", "reach", "sync", "vars"]
    alerter = alert.NTPAlerter(checks)
    while True:
        implementation = process.get_implementation()
        if implementation:
            # run the checks, returning their data
            checkobjs = process.ntpchecks(checks, debug=False, implementation=implementation)
            # alert on the data collected
            alerter.alert(checkobjs=checkobjs, hostname=hostname, interval=args.interval, format=args.mode, debug=debug)

        await asyncio.sleep(get_time_until(args.interval))


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


async def peer_stats_task(args: argparse.Namespace, telegraf: TextIOWrapper) -> None:
    if args.mode != "telegraf":
        # FIXME: add prometheus & collectd implementation
        return

    implementation = None
    logfile = args.logfile
    tailer = None

    while True:
        await asyncio.sleep(0.5)

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
                if "type" not in stats:
                    stats["type"] = find_type(stats["source"], checkobjs["peers"].peers)
                telegraf_line = line_protocol.to_line_protocol(stats, "ntpmon_peer")
                print(telegraf_line, file=telegraf)


async def start_tasks(args: argparse.Namespace, hostname: str, telegraf: TextIOWrapper) -> None:
    alert = asyncio.create_task(alert_task(args, hostname), name="alert")
    stats = asyncio.create_task(peer_stats_task(args, telegraf), name="stats")
    await asyncio.wait((alert, stats), return_when=asyncio.ALL_COMPLETED)


def main():
    args = get_args()

    if "COLLECTD_HOSTNAME" in os.environ:
        args.mode = "collectd"
        hostname = os.environ["COLLECTD_HOSTNAME"]
    else:
        hostname = socket.getfqdn()

    if "COLLECTD_INTERVAL" in os.environ:
        args.mode = "collectd"
        if args.interval is None:
            args.interval = float(os.environ["COLLECTD_INTERVAL"])

    if args.interval is None:
        args.interval = 60

    if not debug:
        if args.mode == "telegraf":
            telegraf_file = get_telegraf_file(args.connect)
            # FIXME: use the file rather than relying on the redirect
            sys.stdout = telegraf_file
        elif args.mode == "prometheus":
            import prometheus_client

            prometheus_client.start_http_server(addr=args.listen_address, port=args.port)
    else:
        telegraf_file = sys.stdout

    asyncio.run(start_tasks(args, hostname, telegraf_file))


if __name__ == "__main__":
    main()
