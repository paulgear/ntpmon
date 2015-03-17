#!/usr/bin/python
#
# Author:       Paul Gear
# Copyright:	(c) 2015 Gear Consulting Pty Ltd <http://libertysys.com.au/>
# License:	GPLv3 <http://www.gnu.org/licenses/gpl.html>
# Description:  Test CheckNTPMon class
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
from check_ntpmon import CheckNTPMon


class TestCheckNTPMon(unittest.TestCase):

    def test_offset(self):
        check = CheckNTPMon()

        for i in [50.01, 50.1, 51, 99, 100, 999]:
            self.assertEqual(check.offset(i), 2, 'High offset non-critical')
            self.assertEqual(check.offset(-i), 2, 'High offset non-critical')

        for i in [10.01, 10.1, 11, 49, 49.99, 50]:
            self.assertEqual(check.offset(i), 1, 'Moderate offset non-warning')
            self.assertEqual(check.offset(-i), 1, 'Moderate offset non-warning')

        for i in [0, 0.01, 1, 1.01, 9, 9.99, 10]:
            self.assertEqual(check.offset(i), 0, 'Low offset non-OK')
            self.assertEqual(check.offset(-i), 0, 'Low offset non-OK')

    def test_peers(self):
        check = CheckNTPMon()

        for i in [-100, -10, -1, 0, 1]:
            self.assertEqual(check.peers(i), 2, 'Low peers non-critical')

        for i in [2, 3]:
            self.assertEqual(check.peers(i), 1, 'Few peers non-warning')

        for i in [4, 5, 6, 10, 100]:
            self.assertEqual(check.peers(i), 0, 'High peers non-OK')

    def test_reach(self):
        check = CheckNTPMon()

        for i in [0, 0.01, 1, 25, 49, 49.99, 50]:
            self.assertEqual(check.reachability(i), 2, 'Low reachability non-critical')
        for i in [50.01, 50.1, 74.99, 75]:
            self.assertEqual(check.reachability(i), 1, 'Moderate reachability non-warning')
        for i in [75.01, 76, 99, 100]:
            self.assertEqual(check.reachability(i), 0, 'High reachability non-OK')
        # check that invalid percentage causes exception
        for i in [-100, -1, 100.01, 101, 1000]:
            self.assertRaises(ValueError, check.reachability, (i))

    def test_sync(self):
        check = CheckNTPMon()

        self.assertFalse(check.sync(''))
        self.assertTrue(check.sync('blah.example.com'))
        self.assertTrue(check.sync('192.168.2.1'))
        self.assertTrue(check.sync('fe80::1'))
        self.assertTrue(check.sync('ds002.dedicated'))
        self.assertTrue(check.sync('node01.au.serve'))


if __name__ == "__main__":
    unittest.main()

