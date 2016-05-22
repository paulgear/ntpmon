#!/usr/bin/env python3
#
# Copyright:    (c) 2016 Paul D. Gear <http://libertysys.com.au/>
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
Classify metrics into OK, WARNING, or CRITICAL ranges.

Create metric definitions like this:
    metricdefs = {
        'offset': ('mid', -50, -10, 10, 50),
        'peers': ('high', 3, 2),
        'reach': ('high', 75, 50),
    }

Create a MetricClassifier:
    mc = MetricClassifier(metricdefs)

Gather your metrics:
    metrics = {
        'offset': -3.467,
        'peers': 3,
        'reach': 48.457,
    }

Ask MetricClassifier to classify them:
    mc.classify_metrics(metrics) == {
        'offset': 'OK',
        'peers': 'WARNING',
        'reach': 'CRITICAL',
    }

MetricClassifier can pick the worst classification, and create a return code for Nagios checks:
    mc.worst_classification() == 'CRITICAL'
    mc.return_code() == 2

"""


def _is_list_numeric(numbers):
    try:
        for x in numbers:
            try:
                float(x)
            except ValueError:
                # parameters must be numeric
                return False
    except Exception:
        return False
    return True


def _is_list_ordered(numbers, order='asc'):
    if order == 'desc':
        last = float('inf')
        for x in numbers:
            if x > last:
                return False
            last = x
    else:
        # order is ascending
        last = float('-inf')
        for x in numbers:
            if x < last:
                return False
            last = x
    return True


def _is_valid_metric_def(metric):
    if metric[0] == 'low':
        return len(metric) == 3 and _is_list_numeric(metric[1:]) and _is_list_ordered(metric[1:])
    elif metric[0] == 'high':
        return len(metric) == 3 and _is_list_numeric(metric[1:]) and _is_list_ordered(metric[1:], order='desc')
    elif metric[0] == 'mid':
        return len(metric) == 5 and _is_list_numeric(metric[1:]) and _is_list_ordered(metric[1:])
    else:
        return False


def _classify_low_metric(value, a, b):
    if value >= b:
        return 'CRITICAL'
    elif value >= a:
        return 'WARNING'
    else:
        return 'OK'


def _classify_high_metric(value, a, b):
    if value <= b:
        return 'CRITICAL'
    elif value <= a:
        return 'WARNING'
    else:
        return 'OK'


def _classify_mid_metric(value, a, b, c, d):
    if value > b and value < c:
        return 'OK'
    elif value > a and value < d:
        return 'WARNING'
    else:
        return 'CRITICAL'


def _classify(value, metricdef):
    try:
        if metricdef[0] == 'low':
            return _classify_low_metric(value, metricdef[1], metricdef[2])
        elif metricdef[0] == 'high':
            return _classify_high_metric(value, metricdef[1], metricdef[2])
        elif metricdef[0] == 'mid':
            return _classify_mid_metric(value, metricdef[1], metricdef[2], metricdef[3], metricdef[4])
    except Exception:
        pass
    return 'UNKNOWN'


def return_code_for_classification(classification):
    if classification == 'OK':
        return 0
    elif classification == 'WARNING':
        return 1
    elif classification == 'CRITICAL':
        return 2
    elif classification == 'UNKNOWN':
        return 3
    else:
        return 99


class MetricClassifier(object):

    def __init__(self, metricdefs):
        self.metricdefs = {}
        for m in metricdefs:
            if _is_valid_metric_def(metricdefs[m]):
                self.metricdefs[m] = metricdefs[m]
            else:
                raise ValueError('Invalid metric definition for %s: %s' % (m, metricdefs[m]))

    def classify(self, metric, value):
        """
        Classify the value of a single metric according to the existing definitions.
        """
        if metric in self.metricdefs:
            return _classify(value, self.metricdefs[metric])
        else:
            raise ValueError('Missing definition for metric %s' % metric)

    def classify_metrics(self, metrics):
        """
        Classify all the metrics in the passed hash according to the existing definitions.
        Return a hash of the results for each metric.
        """
        self.values = metrics
        results = {}
        for m in metrics:
            try:
                results[m] = self.classify(m, metrics[m])
            except Exception:
                results[m] = 'UNKNOWN'
        self.results = results
        return results

    def worst_classification(self, unknown_as_critical=False):
        result = 'UNKNOWN'
        if self.results is not None:
            worst = 0
            for r in self.results:
                rc = return_code_for_classification(self.results[r])
                if rc > worst:
                    worst = rc
                    result = self.results[r]
        if unknown_as_critical and result == 'UNKNOWN':
            return 'CRITICAL'
        else:
            return result

    def return_code(self, unknown_as_critical=False):
        return return_code_for_classification(self.worst_classification(unknown_as_critical))

