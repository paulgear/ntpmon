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
            self.assertEqual(check.offset(i), 2)
            self.assertEqual(check.offset(-i), 2)

        for i in [10.01, 10.1, 11, 49, 49.99, 50]:
            self.assertEqual(check.offset(i), 1)
            self.assertEqual(check.offset(-i), 1)

        for i in [0, 0.01, 1, 1.01, 9, 9.99, 10]:
            self.assertEqual(check.offset(i), 0)
            self.assertEqual(check.offset(-i), 0)

    def test_peers(self):
        check = CheckNTPMon()

        self.assertEqual(check.peers(-100), 2, '-100 peers non-critical')
        self.assertEqual(check.peers(-1), 2, '-10 peers non-critical')
        self.assertEqual(check.peers(0), 2, '0 peers non-critical')
        self.assertEqual(check.peers(1), 2, '1 peer non-critical')

        self.assertEqual(check.peers(2), 1, '2 peers non-warning')
        self.assertEqual(check.peers(3), 1, '3 peers non-warning')

        self.assertEqual(check.peers(4), 0, '4 peers non-OK')
        self.assertEqual(check.peers(5), 0, '5 peers non-OK')
        self.assertEqual(check.peers(6), 0, '6 peers non-OK')
        self.assertEqual(check.peers(10), 0, '10 peers non-OK')
        self.assertEqual(check.peers(100), 0, '100 peers non-OK')

    def test_sync(self):
        check = CheckNTPMon()
        self.assertFalse(check.sync(''))
        self.assertTrue(check.sync('blah.example.com'))
        self.assertTrue(check.sync('192.168.2.1'))
        self.assertTrue(check.sync('fe80::1'))


if __name__ == "__main__":
    unittest.main()

