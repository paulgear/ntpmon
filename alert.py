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

"""
This is the module responsible for setting the classifier levels of metrics,
creating the list of finally-reported metrics (out of all the possible metrics
gathered), and creating messages for display to the user.  It contains a few
special cases which require knowledge of the rest of the application.
"""

import metrics
import pprint

from classifier import MetricClassifier

"""
Aliases for all metrics
"""
_aliases = {
    # peer metrics
    'offset': ('syncpeer-offset-mean', 'survivors-offset-mean', 'backups-offset-mean', 'discards-offset-mean', 'all-offset-mean'),
    'peers': 'all',
    'reach': 'all-reach-mean',
    'sync': 'syncpeer',
    # trace metrics
    'tracehosts': None,
    'traceloops': None,
    # runtime metric
    'runtime': None,
    # readvar metrics
    'frequency': None,
    'rootdelay': None,
    'rootdisp': None,
    'stratum': None,
    'sysjitter': 'sys_jitter',
    'sysoffset': 'offset',
    # return code
    'result': None,
}

"""
Display formats for all metrics
"""
_formats = {
    'offset': (None, 'g'),
    'peers': ('Number of peers', 'd'),
    'reach': ('reachability', '%'),
    'sync': None,
    'tracehosts': (None, 'd'),
    'traceloops': (None, 'd'),
    'runtime': (None, 'd'),
    'frequency': (None, 'g'),
    'rootdelay': (None, 'g'),
    'rootdisp': (None, 'g'),
    'stratum': (None, 'd'),
    'sysjitter': (None, 'g'),
    'sysoffset': (None, 'g'),
    'result': (None, 'd'),
}


"""
Classifications for all metrics
"""
_metricdefs = {
    'runtime': ('high', 512, 0),
    'offset': ('mid', -50, -10, 10, 50),
    'peers': ('high', 3, 1),
    'reach': ('high', 75, 50),
    # sync & trace metrics are integral, but are set to floats
    # in case we ever encounter rounding.
    'sync': ('high', 0.9, 0.9),
    'tracehosts': ('high', 0.1, -0.1),
    'traceloops': ('low', 0.9, 0.9),
    # readvar metrics are reported only, not alerted
}


class NTPAlerter(object):
 
    def __init__(self, checks, objs):
        self.checks = checks
        self.objs = objs
        self.mc = MetricClassifier(_metricdefs)

    def collectmetrics(self, debug):
        self.metrics = {}
        for o in self.objs:
            self.metrics.update(self.objs[o].getmetrics())
        if debug:
            pprint.pprint(self.metrics)
        metrics.addaliases(self.metrics, _aliases)

    def custom_message(self, metric, result):
        """
        Special cases for message formats
        """
        if metric == 'runtime':
            return self.custom_message_runtime(result)
        elif metric == 'sync':
            return self.custom_message_sync(result)
        elif metric == 'tracehosts':
            return self.custom_message_tracehosts(result)
        elif metric == 'traceloops':
            return self.custom_message_traceloops(result)
        return None

    def custom_message_runtime(self, result):
        proc = self.objs['proc']
        if result == 'CRITICAL':
            return '%s: No NTP process could be found.  Please check that an NTP server is installed and running.' % (result,)
        elif result == 'WARNING':
            return 'OK: %s has only been running %d seconds' % (proc.name, proc.getruntime())
        elif result == 'OK':
            return '%s: %s has been running %d seconds' % (result, proc.name, proc.getruntime())
        return None

    def custom_message_sync(self, result):
        if result == 'CRITICAL':
            return '%s: No sync peer selected' % (result,)
        elif result == 'OK':
            return '%s: Time is in sync with %s' % (result, self.objs['peers'].syncpeer())
        return None

    def custom_message_traceloops(self, result):
        if result == 'CRITICAL':
            return '%s: Trace loop detected at host %s' % (result, self.objs['traceloops'].loophost)
        elif result == 'OK':
            return '%s: Trace detected no loops' % (result,)
        return None

    def custom_message_tracehosts(self, result):
        trace = self.objs['trace']
        return '%s: %d hosts detected in trace: %s' % (
            result,
            trace.results['tracehosts'],
            ", ".join(trace.hostlist)
        )

    def alert(self, debug):
        """
        FIXME: explain
        """
        self.collectmetrics(debug)
        results = self.mc.classify_metrics(self.metrics)
        if 'trace' in self.checks:
            self.checks.append('tracehosts')
            self.checks.append('traceloops')
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
            self.metrics['result'] = self.return_code()
            print("%s | %s" % (msgs[m], self.report()))

    def report(self):
        """
        FIXME: explain
        """
        items = []
        for m in sorted(_aliases.keys()):
            if m in self.metrics:
                if _formats[m] is None:
                    fmt = 'g'
                else:
                    fmt = _formats[m][1] if _formats[m][1] != '%' else 'g'
                val = self.mc.fmtstr(fmt) % self.metrics[m]
                items.append("%s=%s" % (m, val))
            else:
                items.append("%s=" % (m,))
        return " ".join(items)

    def return_code(self):
        """
        Don't return anything other than OK until ntpd has been running for
        at least enough time for 8 polling intervals of 64 seconds each.  This
        prevents false positives due to ntpd restarts or short-lived VMs.
        """
        if 'runtime' in self.mc.results and self.mc.results['runtime'] == 'WARNING':
            return 0
        else:
            return self.mc.return_code(self.checks)

