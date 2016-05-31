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

import unittest

from classifier import (
    MetricClassifier,
    return_code_for_classification,
    _classify,
    _is_list_numeric,
    _is_list_ordered,
    _is_valid_metric_def,
)


goodmetricdefs = {
    'a': ('low', 0, 10),
    'b': ('high', 10, 5),
    'c': ('mid', -10, -5, 5, 10),
}

okmetrics = (
    # low metric
    ('a', float('-inf')),
    ('a', -1000),
    ('a', -10),
    ('a', -1),
    ('a', -0.000000001),

    # high metric
    ('b', float('inf')),
    ('b', 1000),
    ('b', 10.000000001),

    # mid metric
    ('c', 0),
    ('c', 1),
    ('c', -1),
    ('c', -4.999999999),
    ('c', 4.999999999),
)

warnmetrics = (
    # low metric
    ('a', 0),
    ('a', 0.0000000001),
    ('a', 1),
    ('a', 5),
    ('a', 9.9999999999),

    # high metric
    ('b', 10),
    ('b', 9.9999999999),
    ('b', 5.0000000001),

    # mid metric
    ('c', -5),
    ('c', 5),
    ('c', -5.000000001),
    ('c', 5.000000001),
    ('c', -6),
    ('c', 6),
    ('c', -9),
    ('c', 9),
    ('c', -9.9999999999),
    ('c', 9.9999999999),
)

criticalmetrics = (
    # low metric
    ('a', 10),
    ('a', 10.0000000001),
    ('a', 100),
    ('a', 343567),
    ('a', float('inf')),

    # high metric
    ('b', 5),
    ('b', 4.999999999),
    ('b', 1),
    ('b', 0.0000000001),
    ('b', 0),
    ('b', -1),
    ('b', -100),
    ('b', -100000),

    # mid metric
    ('c', 10),
    ('c', 10.0000000001),
    ('c', 100),
    ('c', 10000),
    ('c', 343567),
    ('c', float('inf')),
    ('c', -10),
    ('c', -10.0000000001),
    ('c', -100),
    ('c', -10000),
    ('c', -343567),
    ('c', float('-inf')),
)

badmetricdefs = {
    'a': ('low', 10, 0),
    'b': ('high'),
    'c': ('mid', -10, 5, -5, 10),
    'd': ('high', 0, 10),
}

samplemetrics = {
    'a': -10,
    'b': 10,
    'c': 1000.2436542,
    'd': 'hello world!',
}

samplemetricresults = {
    'a': 'OK',
    'b': 'WARNING',
    'c': 'CRITICAL',
    'd': 'UNKNOWN',
}


class TestNTPPeers(unittest.TestCase):
    """
    Test MetricClassifier
    """

    def test_is_list_numeric_good(self):
        l = [0, 3.14159, 'NaN', 1000, -342, 0x123, 0o377, '1000']
        self.assertTrue(_is_list_numeric(l))
        l = {'5678': 'a', '1234': 'c'}
        self.assertTrue(_is_list_numeric(l))

    def test_is_list_numeric_bad(self):
        l = ['0x0123abcdefghij', '0x138f', '3.14159.1', 'NaN', 1000, -342]
        self.assertFalse(_is_list_numeric(l))

    def test_is_list_numeric_empty(self):
        self.assertTrue(_is_list_numeric([]))
        self.assertTrue(_is_list_numeric({}))

    def test_is_list_numeric_wrong_type(self):
        self.assertFalse(_is_list_numeric(None))
        self.assertFalse(_is_list_numeric(True))
        l = {'a': '5678', 'c': '1234'}
        self.assertFalse(_is_list_numeric(l))

    def test_is_list_ordered_good(self):
        l = [0, 1, 2, 3, 4, 5]
        self.assertTrue(_is_list_ordered(l))
        l = [float('inf'), 110, 101, 29, 3, 0.0000000001, -500000]
        self.assertTrue(_is_list_ordered(l, order='desc'))
        l = [float('-inf')]
        self.assertTrue(_is_list_ordered(l))
        l.append(0)
        self.assertTrue(_is_list_ordered(l))
        l.append(float('inf'))
        self.assertTrue(_is_list_ordered(l))
        l = [0]
        self.assertTrue(_is_list_ordered(l))
        l = []
        self.assertTrue(_is_list_ordered(l))

    def test_is_list_ordered_bad(self):
        l = [0, 1, 2, 5, 4, 3]
        self.assertFalse(_is_list_ordered(l))
        self.assertFalse(_is_list_ordered(l, order='desc'))

        l = [110, 101, 29, 3, float('inf'), 0.0000000001, -500000]
        self.assertFalse(_is_list_ordered(l))
        self.assertFalse(_is_list_ordered(l, order='desc'))

        l = [0, float('-inf'), float('inf')]
        self.assertFalse(_is_list_ordered(l))
        self.assertFalse(_is_list_ordered(l, order='desc'))

        l = [1, 0]
        self.assertFalse(_is_list_ordered(l))
        l = [0, 1]
        self.assertFalse(_is_list_ordered(l, order='desc'))

    def test_is_valid_metric_def_good(self):
        for m in goodmetricdefs:
            self.assertTrue(_is_valid_metric_def(goodmetricdefs[m]))

    def test_is_valid_metric_def_bad(self):
        for m in badmetricdefs:
            self.assertFalse(_is_valid_metric_def(badmetricdefs[m]))

    def test_create_good_metricclassifier(self):
        mc = MetricClassifier(goodmetricdefs)
        self.assertNotEqual(mc, None)

    def test_create_bad_metricclassifier(self):
        self.assertRaises(ValueError, MetricClassifier, (badmetricdefs))

    def test_classify_ok_metrics(self):
        for m in okmetrics:
            self.assertEqual(_classify(m[1], goodmetricdefs[m[0]]), 'OK')

    def test_classify_warn_metrics(self):
        for m in warnmetrics:
            self.assertEqual(_classify(m[1], goodmetricdefs[m[0]]), 'WARNING')

    def test_classify_critical_metrics(self):
        for m in criticalmetrics:
            self.assertEqual(_classify(m[1], goodmetricdefs[m[0]]), 'CRITICAL')

    def test_classify_single_metric(self):
        mc = MetricClassifier(goodmetricdefs)
        for m in okmetrics:
            self.assertEqual(mc.classify(m[0], m[1]), 'OK')
        for m in warnmetrics:
            self.assertEqual(mc.classify(m[0], m[1]), 'WARNING')
        for m in criticalmetrics:
            self.assertEqual(mc.classify(m[0], m[1]), 'CRITICAL')

    def test_classify_multiple_metrics(self):
        mc = MetricClassifier(goodmetricdefs)
        self.assertEqual(mc.classify_metrics(samplemetrics), samplemetricresults)

    def test_return_code_for_classification(self):
        returncodes = {
            'OK': 0,
            'WARNING': 1,
            'WARN': 99,
            'warning': 99,
            'CRITICAL': 2,
            'CRIT': 99,
            'error': 99,
            'UNKNOWN': 3,
            'asdf': 99,
            None: 99,
        }
        for r in returncodes:
            self.assertEqual(return_code_for_classification(r), returncodes[r])

    def test_classify_process(self):
        mc = MetricClassifier(goodmetricdefs)
        self.assertEqual(mc.classify_metrics(samplemetrics), samplemetricresults)
        self.assertEqual(mc.worst_classification(), 'UNKNOWN')
        self.assertEqual(mc.worst_classification(unknown_as_critical=True), 'CRITICAL')
        self.assertEqual(mc.return_code(), 3)
        self.assertEqual(mc.return_code(unknown_as_critical=True), 2)


if __name__ == "__main__":
    unittest.main()
