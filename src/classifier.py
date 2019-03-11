
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
Classify metrics into OK, WARNING, or CRITICAL ranges.

Create metric definitions like this:
    metricdefs = {
        'offset': ('mid', -0.05, -0.01, 0.01, 0.05),
        'peers': ('high', 3, 2),
        'reach': ('high', 75, 50),
    }

Create a MetricClassifier:
    mc = MetricClassifier(metricdefs)

Gather metrics:
    metrics = {
        'offset': -0.003467,
        'peers': 3,
        'reach': 48.457,
    }

Ask MetricClassifier to classify them:
    mc.classify_metrics(metrics) == {
        'offset': 'OK',
        'peers': 'WARNING',
        'reach': 'CRITICAL',
    }

MetricClassifier can pick the worst metric and provide a return code for Nagios checks,
and produce human-readable messages:
    mc.worst_metric() == ('reach', 2)
    mc.message('reach', 'reachability', '%') == "CRITICAL: reachability is too low (48.46%) - must be greater than 75%"
"""

import warnings


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

    @staticmethod
    def fmtstr(fmt):
        if fmt == '%':
            # a percentage
            return '%.2f%%'
        elif fmt in 'bcdeEfFgGnoxX':
            # usual python formatter
            return '%' + fmt
        elif len(fmt) > 1 and fmt[0] in '.0123456789':
            # assume we've been given a valid format string with precision
            return '%' + fmt
        else:
            # force string otherwise
            return '%s'

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

    def worst_metric(self, metrics):
        metric = None
        worst = -1
        try:
            for m in metrics:
                if m in self.results:
                    rc = return_code_for_classification(self.results[m])
                    if rc > worst:
                        worst = rc
                        metric = m
        except Exception as e:
            warnings.warn(e)
            metric = 'Unknown'
            worst = 3
        return (metric, worst)

    def return_code(self, metrics, unknown_as_critical=False):
        (metric, rc) = self.worst_metric(metrics)
        if unknown_as_critical and rc == 3:
            return 2
        else:
            return rc

    _formats = {
        'low': '%s: %s is too high (%s) - %s be less than %s',
        'mid': '%s: %s is out of range (%s) - %s be between %s',
        'high': '%s: %s is too low (%s) - %s be greater than %s',
    }

    _must_should = {
        'CRITICAL': 'must',
        'WARNING': 'should',
    }

    def message(self, metric, descr=None, fmt='g'):
        # use base metric name if no long description provided
        if descr is None:
            descr = metric

        # limit fmt to known list of format chars
        fmtstr = MetricClassifier.fmtstr(fmt)

        result = self.results[metric]

        if result in MetricClassifier._must_should:
            # WARNING or CRITICAL
            metrictype = self.metricdefs[metric][0]
            if metrictype not in MetricClassifier._formats:
                raise ValueError('Unknown metric type %s' % metrictype)
            fmtargs = (
                result,
                descr,
                fmtstr % self.values[metric],
                MetricClassifier._must_should[result],
                self.limits(metrictype, metric, result, fmtstr),
            )
            return MetricClassifier._formats[metrictype] % fmtargs
        else:
            # OK or UNKNOWN
            return '%s: %s is %s' % (
                result,
                descr,
                fmtstr % self.values[metric],
            )

    def limits(self, metrictype, metric, result, fmtstr):
        if metrictype == 'mid':
            # mid - WARNING is middle two values, CRITICAL is first & last
            if result == 'CRITICAL':
                low = fmtstr % self.metricdefs[metric][1]
                high = fmtstr % self.metricdefs[metric][4]
            else:
                low = fmtstr % self.metricdefs[metric][2]
                high = fmtstr % self.metricdefs[metric][3]
            return '%s and %s' % (low, high)
        else:
            # high or low - WARNING is first value, CRITICAL second
            if result == 'CRITICAL':
                limit = fmtstr % self.metricdefs[metric][2]
            else:
                limit = fmtstr % self.metricdefs[metric][1]
            return '%s' % limit
