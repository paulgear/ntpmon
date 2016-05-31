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
    'offset': ('syncpeer-offset-mean', 'survivors-offset-mean', 'backups-offset-mean', 'discards-offset-mean', 'ALL-offset-mean'),
    'peers': 'ALL',
    'reach': 'ALL-reach-mean',
    'sync': 'syncpeer',
    # trace metric
    'trace': 'tracerepeats',
    'tracehosts': None,
    # runtime metric
    'runtime': None,
}

"""
Display formats for all metrics
"""
_formats = {
    'offset': (None, 'g'),
    'peers': ('Number of peers', 'd'),
    'reach': ('reachability', '%'),
    'sync': None,
    'trace': None,
    'tracehosts': (None, 'd'),
    'runtime': (None, 'd'),
}


"""
Classifications for all metrics
"""
_metricdefs = {
    'offset': ('mid', -50, -10, 10, 50),
    'peers': ('high', 3, 1),
    'reach': ('high', 75, 50),
    # sync & trace are only 0 or 1, but set to less
    # than 1 just in case we ever encounter rounding.
    'sync': ('high', 0.9, 0.9),
    'trace': ('low', 0.9, 0.9),
    'tracehosts': ('high', 0.1, -0.1),
}


class NTPAlerter(object):
 
    def __init__(self, checks, ntppeers, ntptrace, ntpproc):
        self.checks = checks
        self.ntppeers = ntppeers
        self.ntptrace = ntptrace
        self.ntpproc = ntpproc
        self.mc = MetricClassifier(_metricdefs)

    def collectmetrics(self, debug):
        self.metrics = {}
        self.metrics.update(self.ntppeers.getmetrics())
        for source in (self.ntppeers, self.ntptrace, self.ntpproc):
            self.metrics.update(source.getmetrics())
        if debug:
            pprint.pprint(self.metrics)
        metrics.addaliases(self.metrics, _aliases)

    def custom_message(self, metric, result):
        """
        Special cases for message formats
        """
        if metric == 'sync':
            return self.custom_message_sync(result)
        elif metric == 'trace':
            return self.custom_message_trace(result)
        elif metric == 'tracehosts':
            return self.custom_message_tracehosts(result)
        return None

    def custom_message_sync(self, result):
        if result == 'CRITICAL':
            return '%s: No sync peer selected' % (result,)
        elif result == 'OK':
            return '%s: Time is in sync with %s' % (result, self.ntppeers.syncpeer())
        return None

    def custom_message_trace(self, result):
        if result == 'CRITICAL':
            return '%s: Trace loop detected at host %s' % (result, self.ntptrace.loophost)
        elif result == 'OK':
            return '%s: Trace detected no loops' % (result,)
        return None

    def custom_message_tracehosts(self, result):
        return '%s: %d hosts detected in trace: %s' % (
            result,
            self.ntptrace.results['tracehosts'],
            ", ".join(self.ntptrace.hostlist)
        )

    def alert(self, debug):
        self.collectmetrics(debug)
        results = self.mc.classify_metrics(self.metrics)
        if 'trace' in self.checks:
            # trace implies tracehosts
            self.checks.append('tracehosts')
        msgs = {}
        for metric in self.checks:
            msgs[metric] = self.custom_message(metric, results[metric])
            if msgs[metric] is None:
                msgs[metric] = self.mc.message(metric, _formats[metric][0], _formats[metric][1])
        if debug:
            for m in msgs:
                print(msgs[m])
        else:
            (m, rc) = self.mc.worst_metric(self.checks)
            print(msgs[m])

    def return_code(self):
        return self.mc.return_code(self.checks)

