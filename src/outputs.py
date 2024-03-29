#
# Copyright:    (c) 2023-2024 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>


import argparse
import datetime
import socket
import sys

from io import TextIOWrapper
import time
from typing import ClassVar, Dict, List, Tuple


import line_protocol


class Output:

    peertypes: ClassVar[Dict[str, str]] = {
        "backup": "peers/count-backup",
        "excess": "peers/count-excess",
        "false": "peers/count-false",
        "invalid": "peers/count-invalid",
        "outlier": "peers/count-outlier",
        "pps": "peers/count-pps",
        "survivor": "peers/count-survivor",
        "sync": "peers/count-sync",
    }

    peerstatstypes: ClassVar[Dict[str, str]] = {
        "authenticated": "authenticated/bool",
        "authentication_enabled": "authentication-enabled/bool",
        "authentication_fail": "authentication-fail/bool",
        "bad_header": "bad-header/bool",
        "bogus": "bogus/bool",
        "broadcast": "broadcast/bool",
        "delay": "delay/time_offset",
        "dispersion": "dispersion/time_dispersion",
        "duplicate": "duplicate/bool",
        "exceeded_max_delay": "exceeded-max-delay/bool",
        "exceeded_max_delay_dev_ratio": "exceeded-max-delay-dev-ratio/bool",
        "exceeded_max_delay_ratio": "exceeded-max-delay-ratio/bool",
        "frequency": "frequency/frequency_offset",
        "interleaved": "interleaved/bool",
        "invalid": "invalid/bool",
        "jitter": "jitter/time_offset",
        "leap": "leap/bool",
        "local_poll": "local-poll/gauge",
        "offset": "offset/time_offset",
        "persistent": "persistent/bool",
        "reachable": "reachable/bool",
        "remote_poll": "remote-poll/gauge",
        "root_delay": "rootdelay/root_delay",
        "root_dispersion": "rootdisp/root_dispersion",
        "score": "score/gauge",
        "stratum": "stratum/clock_stratum",
        "sync_loop": "sync-loop/bool",
        "synchronized": "synchronized/bool",
    }

    summarytypes: ClassVar[Dict[str, str]] = {
        "frequency": "frequency/frequency_offset",
        "offset": "offset/time_offset",
        "reach": "reachability/percent",
        "rootdelay": "rootdelay/root_delay",
        "rootdisp": "rootdisp/root_dispersion",
        "runtime": "runtime/duration",
        "stratum": "stratum/clock_stratum",
        "sysjitter": "sysjitter/time_offset",
        "sysoffset": "sysoffset/time_offset",
    }

    def send_info(self, metrics: dict, debug: bool = False) -> None:
        pass

    def send_peer_counts(self, metrics: dict, debug: bool = False) -> None:
        pass

    def send_peer_measurements(self, metrics: dict, debug: bool = False) -> None:
        pass

    def send_summary_stats(self, metrics: dict, debug: bool = False) -> None:
        pass


class CollectdOutput(Output):
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    formatstr: ClassVar[str] = 'PUTVAL "%s/ntpmon-%s" interval=%d N:%.9f'

    def send_peer_counts(self, metrics: dict, debug: bool = False) -> None:
        self.send_stats(metrics, self.peertypes, debug=debug)

    def send_peer_measurements(self, metrics: dict, debug: bool = False) -> None:
        self.send_stats(metrics, self.peerstatstypes, hostname=metrics["source"], debug=debug)

    def send_stats(self, metrics: dict, types: dict, debug: bool = False, hostname: str = None) -> None:
        if hostname is None:
            hostname = self.args.hostname
        for metric in sorted(types.keys()):
            if metric in metrics and types[metric] is not None:
                print(self.formatstr % (hostname, types[metric], self.args.interval, metrics[metric]))

    def send_summary_stats(self, metrics: dict, debug: bool = False) -> None:
        self.send_stats(metrics, self.summarytypes, debug=debug)


class PrometheusOutput(Output):
    def __init__(self, args: argparse.Namespace) -> None:
        self.prometheus_objs = {}
        import prometheus_client

        prometheus_client.start_http_server(addr=args.listen_address, port=args.port)

    infolabels: ClassVar[List[str]] = [
        "implementation_name",
        "implementation_version",
        "ntpmon_version",
        "platform_machine",
        "platform_release",
        "platform_system",
        "python_version",
    ]

    infotypes: ClassVar[Dict[str, Tuple[str, str, str]]] = {
        "resident_set_size": ("i", "_bytes", "The resident set size of the ntpmon process"),
        "virtual_memory_size": ("i", "_bytes", "The virtual memory size of the ntpmon process"),
    }

    infotypes_labelled: ClassVar[Dict[str, Tuple[str, str, str]]] = {
        "uptime": (None, "_seconds", "Time for which the ntpmon process has been running"),
    }

    info_rewrites: ClassVar[Dict[str, str]] = {
        "ntpmon_rss": "resident_set_size",
        "ntpmon_uptime": "uptime",
        "ntpmon_vms": "virtual_memory_size",
    }

    peerstatslabels: ClassVar[List[str]] = [
        "mode",
        "peertype",
        "refid",
        "rx_timestamp",
        "source",
        "tx_timestamp",
    ]

    peerstatstypes: ClassVar[Dict[str, Tuple[str, str, str]]] = {
        "authenticated": ("i", None, "Whether the peer is authenticated"),
        "authentication_enabled": ("i", None, "Whether the peer has authentication enabled"),
        "authentication_fail": ("i", None, "Whether the peer has failed authentication"),
        "bad_header": ("i", None, "Whether the peer has sent bad header data"),
        "bogus": ("i", None, "Whether the peer has has been marked as bogus"),
        "broadcast": ("i", None, "Whether the peer is a broadcast association"),
        "delay": (None, "_seconds", "Network round trip delay to this peer"),
        "dispersion": (None, "_seconds", "Calculated uncertainty for this peer"),
        "duplicate": ("i", None, "Whether the peer's last response is a duplicate"),
        "exceeded_max_delay": ("i", None, "Whether the peer has exceeded the chrony maximum delay"),
        "exceeded_max_delay_dev_ratio": ("i", None, "Whether the peer has exceeded the chrony maximum delay dev ratio"),
        "exceeded_max_delay_ratio": ("i", None, "Whether the peer has exceeded the chrony maximum delay ratio"),
        "frequency": (None, "_hertz", "Estimated frequency error of this peer's clock"),
        "interleaved": ("i", None, "Whether the peer has interleaving enabled"),
        "invalid": ("i", None, "Whether the peer has failed validity checks"),
        "jitter": (None, "_seconds", "RMS average of peer offset differences"),
        "leap": ("i", None, "Whether the peer has asserted its leap indicator"),
        "local_poll": ("i", None, "Rate at which local host polls this peer"),
        "offset": (None, "_seconds", "Current clock offset of this peer"),
        "persistent": ("i", None, "Whether the peer is configured as a persistent association"),
        "reachable": ("i", None, "Whether the peer is reachable"),
        "remote_poll": ("i", None, "The poll rate reported by this peer"),
        "root_delay": (None, "_seconds", "The root delay reported by this peer"),
        "root_dispersion": (None, "_seconds", "The root dispersion reported by this peer"),
        "score": (None, None, "The chrony score calculated for this peer"),
        "stratum": ("i", None, "The stratum reported by this peer"),
        "sync_loop": ("i", None, "Whether a synchronization loop has been detected for this peer"),
        "synchronized": ("i", None, "Whether the peer reports as synchronized"),
    }

    summarystatstypes: ClassVar[Dict[str, Tuple[str, str, str]]] = {
        "frequency": (None, "_hertz", "Frequency error of the local clock"),
        "offset": (None, "_seconds", "Mean clock offset of peers"),
        "reach": ("%", "_ratio", "Peer reachability over the last 8 polls"),
        "rootdelay": (None, "_seconds", "Network delay to stratum 0 sources"),
        "rootdisp": (None, "_seconds", "Maximum calculated uncertainty from stratum 0 sources"),
        "runtime": (None, "_duration_seconds", "Duration NTP service has been running"),
        "stratum": ("i", None, "NTP stratum of this server"),
        "sysjitter": (None, "_seconds", "RMS average of most recent system peer offset differences"),
        "sysoffset": (None, "_seconds", "Current clock offset of selected system peer"),
    }

    def send_info(self, metrics: dict, debug: bool = False) -> None:
        # rewrite info metric names for prometheus
        for i in self.info_rewrites:
            if i in metrics:
                metrics[self.info_rewrites[i]] = metrics[i]
                del metrics[i]
        self.send_stats("ntpmon", metrics, self.infotypes, [], [], debug=debug)
        self.send_stats(
            "ntpmon",
            metrics,
            self.infotypes_labelled,
            [x for x in self.infolabels if x in metrics],
            [metrics[x] for x in self.infolabels if x in metrics],
            debug=debug,
        )

    def send_peer_counts(self, metrics: dict, debug: bool = False) -> None:
        for metric in sorted(self.peertypes.keys()):
            if metric in metrics:
                self.set_prometheus_metric(
                    "ntpmon_peers",
                    "NTP peer count",
                    metrics[metric],
                    "%d",
                    labelnames=["peertype"],
                    labels=[metric],
                    debug=debug,
                )

    def send_peer_measurements(self, metrics: dict, debug: bool = False) -> None:
        self.send_stats(
            "ntpmon_peer",
            metrics,
            self.peerstatstypes,
            [x for x in self.peerstatslabels if x in metrics],
            [metrics[x] for x in self.peerstatslabels if x in metrics],
            debug=debug,
        )

    def send_stats(
        self,
        prefix: str,
        metrics: dict,
        metrictypes: dict,
        labelnames: List[str] = [],
        labels: List[str] = [],
        debug: bool = False,
    ) -> None:
        for metric in sorted(metrictypes.keys()):
            if metric in metrics:
                (datatype, suffix, description) = metrictypes[metric]
                name = prefix + "_" + line_protocol.transform_identifier(metric)
                if suffix is not None:
                    name += suffix
                value = metrics[metric]
                fmt = "%.9f"
                if datatype == "i":
                    fmt = "%d"
                elif datatype == "%":
                    value /= 100
                self.set_prometheus_metric(name, description, value, fmt, labelnames, labels, debug=debug)

    def send_summary_stats(self, metrics: dict, debug: bool = False) -> None:
        self.send_stats("ntpmon", metrics, self.summarystatstypes, debug=debug)

    def set_prometheus_metric(
        self,
        name: str,
        description: str,
        value: float,
        fmt: str,
        labelnames: List[str],
        labels: List[str],
        debug: bool = False,
    ) -> None:
        import prometheus_client

        if debug:
            print("# HELP %s %s" % (name, description))
            print("# TYPE %s gauge" % (name,))
            labelstr = ",".join([k + '="' + v + '"' for k, v in zip(labelnames, labels)])
            if len(labelstr):
                labelstr = "{" + labelstr + "}"
            valuestr = fmt % (value,)
            print("%s%s %s" % (name, labelstr, valuestr))
            return

        if name not in self.prometheus_objs:
            g = prometheus_client.Gauge(name, description, labelnames)
            self.prometheus_objs[name] = g
        else:
            g = self.prometheus_objs[name]

        if len(labels):
            g = g.labels(*labels)

        g.set(value)


class TelegrafOutput(Output):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__()
        self.args = args
        self.set_file()

    @staticmethod
    def get_telegraf_file(connect: str) -> TextIOWrapper:
        """Return a TextIOWrapper for writing data to telegraf"""
        (host, port) = connect.split(":")
        port = int(port)
        s = socket.socket()
        s.connect((host, port))
        return s.makefile(mode="w")

    def send(self, name: str, metrics: dict, tries: int = 0) -> None:
        telegraf_line = line_protocol.to_line_protocol(metrics, name)
        if tries >= 5:
            print("Reached maximum retries on telegraf connection", file=sys.stderr)
            print(telegraf_line)
            sys.exit(3)
        try:
            print(telegraf_line, file=self.file)
        except BrokenPipeError as bpe:
            # If we have lost our connection to telegraf, wait a little, then
            # reopen the socket and try again.
            time.sleep(0.1)
            self.set_file()
            self.send(name, metrics, tries + 1)

    def send_info(self, metrics: dict, debug: bool) -> None:
        self.send("ntpmon_info", metrics)

    def send_peer_counts(self, metrics: dict, debug: bool = False) -> None:
        for metric in sorted(self.peertypes.keys()):
            telegraf_metrics = {
                "count": metrics[metric],
                "peertype": metric,
            }
            self.send("ntpmon_peers", telegraf_metrics)

    def send_peer_measurements(self, metrics: dict, debug: bool = False) -> None:
        self.send("ntpmon_peer", metrics)

    def send_summary_stats(self, metrics: dict, debug: bool = False) -> None:
        telegraf_metrics = {k: metrics[k] for k in sorted(self.summarytypes.keys()) if k in metrics}
        self.send("ntpmon", telegraf_metrics)

    def set_file(self) -> None:
        self.file = sys.stdout if self.args.debug else self.get_telegraf_file(self.args.connect)


def get_output(args: argparse.Namespace) -> Output:
    if args.mode == "collectd":
        return CollectdOutput(args)
    elif args.mode == "prometheus":
        return PrometheusOutput(args)
    elif args.mode == "telegraf":
        return TelegrafOutput(args)
    else:
        raise ValueError("Unknown output mode")
