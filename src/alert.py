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

import metrics
import outputs
import version

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


class NTPAlerter(object):
    def __init__(self, checks):
        self.checks = checks
        self.mc = MetricClassifier(_metricdefs)
        self.metrics = {}
        self.objs = {}

    def alert(self, checkobjs: dict, output: outputs.Output, debug: bool = False) -> None:
        """
        Produce the metrics
        """
        if "info" in checkobjs:
            output.send_info(checkobjs["info"], debug)
            del checkobjs["info"]
        self.collectmetrics(checkobjs=checkobjs)
        self.mc.classify_metrics(self.metrics)
        (m, rc) = self.mc.worst_metric(self.checks)
        self.metrics["result"] = self.return_code()
        output.send_summary_stats(self.metrics, debug)
        output.send_peer_counts(self.metrics, debug)

    def collectmetrics(self, checkobjs: dict, debug: bool = False) -> None:
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
