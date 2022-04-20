
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
import sys

from classifier import MetricClassifier


"""
Aliases for all metrics
"""
_aliases = {
    # peer metrics
    'offset': ('survivor-offset-mean', 'outlier-offset-mean', 'backup-offset-mean', 'all-offset-mean'),
    'peers': 'all',
    'reach': 'all-reach-mean',
    'sync': None,
    # trace metrics
    'tracehosts': None,
    'traceloops': None,
    'tracetime': None,
    # runtime metric
    'runtime': None,
    # readvar metrics
    'frequency': None,
    'rootdelay': None,
    'rootdisp': None,
    'stratum': None,
    # these are aliased within the readvar module to prevent clashes
    'sysjitter': None,
    'sysoffset': None,
    # return code
    'result': None,
}

"""
Display formats for all metrics
"""
_formats = {
    'offset': (None, 'f'),
    'peers': ('Number of peers', 'd'),
    'reach': ('reachability', '%'),
    'sync': None,
    'tracehosts': (None, 'd'),
    'traceloops': (None, 'd'),
    'tracetime': (None, 'f'),
    'runtime': (None, 'd'),
    'frequency': (None, 'f'),
    'rootdelay': (None, 'f'),
    'rootdisp': (None, 'f'),
    'stratum': (None, 'd'),
    'sysjitter': (None, '.9f'),
    'sysoffset': (None, '.9f'),
    'result': (None, 'd'),
}


"""
Classifications for all metrics
"""
_metricdefs = {
    'runtime': ('high', 512, 0),
    'offset': ('mid', -0.05, -0.01, 0.01, 0.05),
    'peers': ('high', 3, 1),
    'reach': ('high', 75, 50),
    # sync & trace metrics are integral, but are set to floats
    # in case we ever encounter rounding.
    'sync': ('high', 0.9, 0.9),
    'tracehosts': ('high', 0.1, -0.1),
    'traceloops': ('low', 0.9, 0.9),
    # readvar metrics are normally reported only, not alerted
    # however, if only vars is checked, we report on sysoffset
    'sysoffset': ('mid', -0.05, -0.01, 0.01, 0.05),
}


"""
Metric types for collectd
"""
_collectdtypes = {

    'frequency': 'frequency/frequency_offset',
    'offset': 'offset/time_offset',
    'reach': 'reachability/percent',
    'rootdelay': 'rootdelay/time_offset',
    'rootdisp': 'rootdisp/time_offset',
    'runtime': 'runtime/duration',
    'stratum': 'stratum/count',
    'sysjitter': 'sysjitter/time_offset',
    'sysoffset': 'sysoffset/time_offset',
    'tracehosts': 'tracehosts/count',
    'traceloops': 'traceloops/count',
    'tracetime': 'runtime/duration',

}


"""
Peer metric types, used by both collectd & telegraf
"""
_peer_types = {

    'backup': 'peers/count-backup',
    'excess': 'peers/count-excess',
    'false': 'peers/count-false',
    'invalid': 'peers/count-invalid',
    'outlier': 'peers/count-outlier',
    'pps': 'peers/count-pps',
    'survivor': 'peers/count-survivor',
    'sync': 'peers/count-sync',

}

"""
Metric types for telegraf
"""
_telegraf_types = {

    'frequency': None,
    'offset': None,
    'reach': None,
    'rootdelay': None,
    'rootdisp': None,
    'runtime': None,
    'stratum': 'i',
    'sysjitter': None,
    'sysoffset': None,
    'tracehosts': 'i',
    'traceloops': 'i',
    'tracetime': None,

}


class NTPAlerter(object):
 
    def __init__(self, checks):
        self.checks = checks
        self.mc = MetricClassifier(_metricdefs)
        self.metrics = {}
        self.objs = {}

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
        if 'proc' in self.checks:
            self.checks.append('runtime')
        if 'trace' in self.checks:
            self.checks.append('tracehosts')
            self.checks.append('traceloops')
            self.checks.append('tracetime')
        if 'vars' in self.checks and 'offset' not in self.checks:
            self.checks.append('sysoffset')

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
            return ('%s: No NTP process could be found.'
                    '  Please check that an NTP server is installed and running.') % (result,)
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
            return '%s: Trace loop detected at host %s' % (result, self.objs['trace'].loophost)
        elif result == 'OK':
            return '%s: Trace detected no loops' % (result,)
        return None

    def custom_message_tracehosts(self, result):
        trace = self.objs['trace']
        return '%s: %d hosts detected in trace: %s' % (
            result,
            trace.results['tracehosts'],
            ', '.join(trace.hostlist)
        )

    def alert(self, checkobjs, hostname, interval, format):
        """
        Produce the metrics
        """
        self.collectmetrics(checkobjs=checkobjs, debug=False)
        self.mc.classify_metrics(self.metrics)
        (m, rc) = self.mc.worst_metric(self.checks)
        self.metrics['result'] = self.return_code()
        if format == 'collectd':
            self.alert_collectd(hostname, interval)
        elif format == 'telegraf':
            self.alert_telegraf()
        self.alert_peers(hostname, interval, format)
        self.finished_output()

    def alert_collectd(self, hostname, interval):
        """
        Produce collectd output for the metrics
        """
        for metric in sorted(_collectdtypes.keys()):
            if metric in self.metrics:
                print('PUTVAL "%s/ntpmon-%s" interval=%d N:%.9f' % (
                    hostname,
                    _collectdtypes[metric],
                    interval,
                    self.metrics[metric],
                ))

    def alert_telegraf(self):
        print('ntpmon ', end='')
        telegraf_metrics = []
        for metric in sorted(_telegraf_types.keys()):
            if metric in self.metrics:
                s = metric + '='
                if _telegraf_types[metric] == 'i':
                    s += '%di' % (self.metrics[metric],)
                else:
                    s += '%.9f' % (self.metrics[metric],)
                telegraf_metrics.append(s)
        print(','.join(telegraf_metrics))

    def alert_peers(self, hostname, interval, format):
        for metric in _peer_types:
            value = self.metrics.get(metric)
            if format == 'collectd':
                print('PUTVAL "%s/ntpmon-%s" interval=%d N:%.9f' % (
                    hostname,
                    _peer_types[metric],
                    interval,
                    value,
                ))
            elif format == 'telegraf':
                print('ntpmon_peers,peertype=%s count=%di' % (metric, value))

    @staticmethod
    def finished_output():
        if sys.stdout.isatty():
            # we're outputting to a terminal; must be test mode
            print('')
        else:
            # flush standard output to ensure metrics are sent immediately
            sys.stdout.flush()

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
            self.metrics['result'] = self.return_code()
            print('%s | %s' % (msgs[m], self.report()))

    def report(self):
        """
        Report metric values.
        """
        items = []
        for m in sorted(_aliases.keys()):
            if m in self.metrics:
                if _formats[m] is None:
                    fmt = 'f'
                else:
                    fmt = _formats[m][1] if _formats[m][1] != '%' else 'f'
                val = self.mc.fmtstr(fmt) % self.metrics[m]
                items.append('%s=%s' % (m, val))
            else:
                items.append('%s=' % (m,))
        return ' '.join(items)

    def return_code(self):
        """
        Don't return anything other than OK until the NTP daemon has been running
        for at least enough time for 8 polling intervals of 64 seconds each.  This
        prevents false positives due to restarts or short-lived VMs.
        """
        if 'runtime' in self.mc.results and self.mc.results['runtime'] == 'WARNING':
            return 0
        else:
            return self.mc.return_code(self.checks)
