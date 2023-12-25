#
# Copyright:    (c) 2016-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

"""
This is the module responsible for setting the classifier levels of metrics,
creating the list of finally-reported metrics (out of all the possible metrics
gathered), and creating messages for display to the user.  It contains a few
special cases which require knowledge of the rest of the application.
"""

import pprint
import sys

import line_protocol
import metrics

from io import TextIOWrapper

from classifier import MetricClassifier


"""
Aliases for all metrics
"""
_aliases = {
    # peer metrics
    "offset": ("survivor-offset-mean", "outlier-offset-mean", "backup-offset-mean", "all-offset-mean"),
    "peers": "all",
    "reach": "all-reach-mean",
    "sync": None,
    # runtime metric
    "runtime": None,
    # readvar metrics
    "frequency": None,
    "rootdelay": None,
    "rootdisp": None,
    "stratum": None,
    # these are aliased within the readvar module to prevent clashes
    "sysjitter": None,
    "sysoffset": None,
    # return code
    "result": None,
}

"""
Display formats for all metrics
"""
_formats = {
    "offset": (None, "f"),
    "peers": ("Number of peers", "d"),
    "reach": ("reachability", "%"),
    "sync": None,
    "runtime": (None, "d"),
    "frequency": (None, "f"),
    "rootdelay": (None, "f"),
    "rootdisp": (None, "f"),
    "stratum": (None, "d"),
    "sysjitter": (None, ".9f"),
    "sysoffset": (None, ".9f"),
    "result": (None, "d"),
}


"""
Classifications for all metrics
"""
_metricdefs = {
    "runtime": ("high", 512, 0),
    "offset": ("mid", -0.05, -0.01, 0.01, 0.05),
    "peers": ("high", 3, 1),
    "reach": ("high", 75, 50),
    # sync is integral, but set to float in case we ever encounter rounding.
    "sync": ("high", 0.9, 0.9),
    # readvar metrics are normally reported only, not alerted
    # however, if only vars is checked, we report on sysoffset
    "sysoffset": ("mid", -0.05, -0.01, 0.01, 0.05),
}


"""
Metric types for collectd
"""
_collectdtypes = {
    "frequency": "frequency/frequency_offset",
    "offset": "offset/time_offset",
    "reach": "reachability/percent",
    "rootdelay": "rootdelay/time_offset",
    "rootdisp": "rootdisp/time_offset",
    "runtime": "runtime/duration",
    "stratum": "stratum/count",
    "sysjitter": "sysjitter/time_offset",
    "sysoffset": "sysoffset/time_offset",
}


"""
Peer metric types, used by both collectd & telegraf
"""
_peer_types = {
    "backup": "peers/count-backup",
    "excess": "peers/count-excess",
    "false": "peers/count-false",
    "invalid": "peers/count-invalid",
    "outlier": "peers/count-outlier",
    "pps": "peers/count-pps",
    "survivor": "peers/count-survivor",
    "sync": "peers/count-sync",
}

"""
Metric types and suffixes for prometheus
"""
_prometheus_types = {
    "frequency": (None, "_hertz", "Frequency error of the local clock"),
    "offset": (None, "_seconds", "Mean clock offset of peers"),
    "reach": ("%", "_ratio", "Peer reachability over the last 8 polls"),
    "rootdelay": (None, "_seconds", "Network delay to stratum 0 sources"),
    "rootdisp": (None, "_seconds", "Maximum calculated offset from stratum 0 sources"),
    "runtime": (None, "_duration_seconds", "Duration NTP service has been running"),
    "stratum": ("i", None, "NTP stratum of this server"),
    "sysjitter": (None, "_seconds", "RMS average of most recent system peer offset differences"),
    "sysoffset": (None, "_seconds", "Current clock offset of selected system peer"),
}

"""
Metric types for telegraf
"""
_telegraf_types = {
    "frequency": None,
    "offset": None,
    "reach": None,
    "rootdelay": None,
    "rootdisp": None,
    "runtime": None,
    "stratum": "i",
    "sysjitter": None,
    "sysoffset": None,
}


class NTPAlerter(object):
    def __init__(self, checks):
        self.checks = checks
        self.mc = MetricClassifier(_metricdefs)
        self.metrics = {}
        self.objs = {}
        self.prometheus_objs = {}

    def collectmetrics(self, checkobjs, debug):
        """
        Get metrics from each registered metric source and add all relevant aliases.
        """
        self.metrics = {}
        if checkobjs is None:
            return
        self.objs = checkobjs
        for o in self.objs:
            self.metrics.update(self.objs[o].getmetrics())
        if debug:
            pprint.pprint(self.metrics)
        metrics.addaliases(self.metrics, _aliases)
        if "proc" in self.checks:
            self.checks.append("runtime")
        if "vars" in self.checks and "offset" not in self.checks:
            self.checks.append("sysoffset")

    def custom_message(self, metric, result):
        """
        Special cases for message formats
        """
        if metric == "runtime":
            return self.custom_message_runtime(result)
        elif metric == "sync":
            return self.custom_message_sync(result)
        return None

    def custom_message_runtime(self, result):
        proc = self.objs["proc"]
        if result == "CRITICAL":
            return "%s: No NTP process could be found.  Please check that an NTP server is installed and running." % (result,)
        elif result == "WARNING":
            return "OK: %s has only been running %d seconds" % (proc.name, proc.getruntime())
        elif result == "OK":
            return "%s: %s has been running %d seconds" % (result, proc.name, proc.getruntime())
        return None

    def custom_message_sync(self, result):
        if result == "CRITICAL":
            return "%s: No sync peer selected" % (result,)
        elif result == "OK":
            return "%s: Time is in sync with %s" % (result, self.objs["peers"].syncpeer())
        return None

    def alert(self, checkobjs, hostname, interval, format, telegraf_file, debug=False):
        """
        Produce the metrics
        """
        self.collectmetrics(checkobjs=checkobjs, debug=False)
        self.mc.classify_metrics(self.metrics)
        (m, rc) = self.mc.worst_metric(self.checks)
        self.metrics["result"] = self.return_code()
        if format == "collectd":
            self.alert_collectd(hostname, interval)
        elif format == "prometheus":
            self.alert_prometheus(debug=debug)
        elif format == "telegraf":
            self.alert_telegraf(telegraf_file)
        self.alert_peers(hostname, interval, format, telegraf_file, debug)

    def alert_collectd(self, hostname, interval):
        """
        Produce collectd output for the metrics
        """
        for metric in sorted(_collectdtypes.keys()):
            if metric in self.metrics:
                print(
                    'PUTVAL "%s/ntpmon-%s" interval=%d N:%.9f'
                    % (
                        hostname,
                        _collectdtypes[metric],
                        interval,
                        self.metrics[metric],
                    )
                )

    def set_prometheus_metric(self, name, description, value, peertype=None):
        import prometheus_client

        if name in self.prometheus_objs:
            g = self.prometheus_objs[name]
            if peertype is not None:
                g = g.labels(peertype=peertype)
        else:
            if peertype is not None:
                g = prometheus_client.Gauge(name, description, ["peertype"])
                self.prometheus_objs[name] = g
                g = g.labels(peertype=peertype)
            else:
                g = prometheus_client.Gauge(name, description)
                self.prometheus_objs[name] = g
        g.set(value)

    def alert_prometheus(self, debug=False):
        def emit_metric(name, description, metrictype, value, format):
            if debug:
                valuestr = format % (value,)
                print("# HELP %s %s" % (name, description))
                print("# TYPE %s gauge" % (name,))
                print("%s %s" % (name, valuestr))
            else:
                self.set_prometheus_metric(name, description, value)

        for metric in sorted(_prometheus_types.keys()):
            if metric in self.metrics:
                (metrictype, suffix, description) = _prometheus_types[metric]
                s = "ntpmon_" + metric
                if suffix is not None:
                    s += suffix
                val = self.metrics[metric]
                fmt = "%.9f"
                if metrictype == "i":
                    fmt = "%d"
                elif metrictype == "%":
                    val /= 100
                emit_metric(s, description, metrictype, val, fmt)

    def alert_telegraf(self, telegraf_file: TextIOWrapper):
        telegraf_metrics = {k: self.metrics[k] for k in sorted(_telegraf_types.keys()) if k in self.metrics}
        output = line_protocol.to_line_protocol(telegraf_metrics, "ntpmon")
        print(output, file=telegraf_file)

    def alert_peers(self, hostname, interval, format, telegraf_file, debug=False):
        if debug and format == "prometheus":
            print("# TYPE ntpmon_peers gauge")
        for metric in _peer_types:
            value = self.metrics.get(metric)
            if format == "collectd":
                print(
                    'PUTVAL "%s/ntpmon-%s" interval=%d N:%.9f'
                    % (
                        hostname,
                        _peer_types[metric],
                        interval,
                        value,
                    )
                )
            elif format == "prometheus":
                if debug:
                    print('ntpmon_peers{peertype="%s"} %d' % (metric, value))
                else:
                    self.set_prometheus_metric("ntpmon_peers", "NTP peer count", value, metric)
            elif format == "telegraf":
                telegraf_metrics = {
                    "count": value,
                    "peertype": metric,
                }
                output = line_protocol.to_line_protocol(telegraf_metrics, "ntpmon_peers")
                print(output, file=telegraf_file)

    def alert_nagios(self, checkobjs, debug):
        """
        Produce nagios output for the metrics
        """
        self.collectmetrics(checkobjs=checkobjs, debug=debug)
        results = self.mc.classify_metrics(self.metrics)
        msgs = {}
        for metric in self.checks:
            if metric in results:
                msgs[metric] = self.custom_message(metric, results[metric])
                if msgs[metric] is None:
                    msgs[metric] = self.mc.message(metric, _formats[metric][0], _formats[metric][1])
        if debug:
            for m in msgs:
                print(msgs[m])
        else:
            (m, rc) = self.mc.worst_metric(self.checks)
            self.metrics["result"] = self.return_code()
            print("%s | %s" % (msgs[m], self.report()))

    def report(self):
        """
        Report metric values.
        """
        items = []
        for m in sorted(_aliases.keys()):
            if m in self.metrics:
                if _formats[m] is None:
                    fmt = "f"
                else:
                    fmt = _formats[m][1] if _formats[m][1] != "%" else "f"
                val = self.mc.fmtstr(fmt) % self.metrics[m]
                items.append("%s=%s" % (m, val))
        return " ".join(items)

    def return_code(self):
        """
        Don't return anything other than OK until the NTP daemon has been running
        for at least enough time for 8 polling intervals of 64 seconds each.  This
        prevents false positives due to restarts or short-lived VMs.
        """
        if "runtime" in self.mc.results and self.mc.results["runtime"] == "WARNING":
            return 0
        else:
            return self.mc.return_code(self.checks)
