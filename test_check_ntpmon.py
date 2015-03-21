#!/usr/bin/python
#
# Author:       Paul Gear
# Copyright:    (c) 2015 Gear Consulting Pty Ltd <http://libertysys.com.au/>
# License:      GPLv3 <http://www.gnu.org/licenses/gpl.html>
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
from check_ntpmon import CheckNTPMon, NTPPeers

testdata = [
"""
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 137.189.4.10    .STEP.          16 u    - 1024    0    0.000    0.000   0.000
 128.199.253.156 .STEP.          16 u    - 1024    0    0.000    0.000   0.000
 103.233.241.1   .STEP.          16 u    - 1024    0    0.000    0.000   0.000
 128.199.169.185 .STEP.          16 u    - 1024    0    0.000    0.000   0.000
*91.189.89.199   131.188.3.220    2 u 1019 1024  377  346.845   -0.598   1.105
 192.189.54.33   .STEP.          16 u    - 1024    0    0.000    0.000   0.000
 129.250.35.250  .STEP.          16 u    - 1024    0    0.000    0.000   0.000
 27.54.95.11     .STEP.          16 u    - 1024    0    0.000    0.000   0.000
 54.252.129.186  .STEP.          16 u    - 1024    0    0.000    0.000   0.000
""",
"""
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
-203.19.252.1    210.9.192.50     2 u  456 1024  377   47.629   -1.526  35.084
*202.60.94.11    223.252.32.9     2 u  618 1024  377   18.785    0.259   0.371
+202.60.94.15    223.252.32.9     2 u  635 1024  377   19.333    0.038   0.851
+54.252.129.186  223.252.32.9     2 u  927 1024  377   36.072    0.337   1.043
-192.168.1.2     203.23.237.200   3 u  788 1024  377    0.627   -0.605   0.162
-192.168.1.1     203.23.237.200   3 u  123 1024  377    0.299   -0.941   0.329
 192.168.1.21    .INIT.          16 u    - 1024    0    0.000    0.000   0.000
""",
"""
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*91.189.94.4     131.188.3.220    2 u  338 1024  377    1.600  -194.54 171.548
""",
"""
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 218.189.210.3   .INIT.          16 u    -   64    0    0.000    0.000   0.000
 103.224.117.98  .INIT.          16 u    -   64    0    0.000    0.000   0.000
 118.143.17.82   .INIT.          16 u    -   64    0    0.000    0.000   0.000
 91.189.89.199   192.93.2.20      2 u   21   64    7  336.631    0.913   0.223
 175.45.85.97    .INIT.          16 u    -   64    0    0.000    0.000   0.000
 192.189.54.33   .INIT.          16 u    -   64    0    0.000    0.000   0.000
 129.250.35.250  .INIT.          16 u    -   64    0    0.000    0.000   0.000
 54.252.165.245  .INIT.          16 u    -   64    0    0.000    0.000   0.000
""",
]


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

        self.assertEqual(check.sync(''), 2, 'Invalid sync peer not detected')
        self.assertEqual(check.sync('    '), 2, 'Invalid sync peer not detected')
        self.assertEqual(check.sync('!@#$%^&*()'), 2, 'Invalid sync peer not detected')
        self.assertEqual(check.sync('blah.example.com'), 0, 'Sync peer not detected')
        self.assertEqual(check.sync('192.168.2.1'), 0, 'Sync peer not detected')
        self.assertEqual(check.sync('fe80::1'), 0, 'Sync peer not detected')
        self.assertEqual(check.sync('ds002.dedicated'), 0, 'Sync peer not detected')
        self.assertEqual(check.sync('node01.au.serve'), 0, 'Sync peer not detected')

    def test_NTPPeer0(self):
        # check the parsing done by NTPPeers
        ntp = NTPPeers(testdata[0].split("\n"))
        self.assertEqual(ntp.ntpdata['syncpeer'], '91.189.89.199')
        self.assertEqual(ntp.ntpdata['offsetsyncpeer'], 0.598)
        self.assertEqual(ntp.ntpdata['survivors'], 1)
        self.assertEqual(ntp.ntpdata['averageoffsetsurvivors'], 0.598)
        self.assertEqual(ntp.ntpdata['discards'], 8)
        self.assertEqual(ntp.ntpdata['averageoffsetdiscards'], 0)
        self.assertEqual(ntp.ntpdata['peers'], 9)
        self.assertEqual(ntp.ntpdata['averageoffset'], 0.06644444444444444)
        self.assertEqual(ntp.ntpdata['reachability'], 11.11111111111111)

        # run checks on the data
        check = CheckNTPMon()
        self.assertEqual(check.sync(ntp.ntpdata['syncpeer']), 0, 'Sync peer not detected')
        self.assertEqual(check.offset(ntp.ntpdata['offsetsyncpeer']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetsurvivors']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetdiscards']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffset']), 0, 'Low offset non-OK')
        self.assertEqual(check.peers(ntp.ntpdata['peers']), 0, 'High peers non-OK')
        self.assertEqual(check.reachability(ntp.ntpdata['reachability']), 2,
                         'Low reachability non-critical')

        # run overall health checks
        self.assertEqual(ntp.check_sync(), 0, 'Sync peer not detected')
        self.assertEqual(ntp.check_offset(), 0, 'Low offset non-OK')
        self.assertEqual(ntp.check_peers(), 0, 'High peers non-OK')
        self.assertEqual(ntp.check_reachability(), 2, 'Low reachability non-critical')

    def test_NTPPeer1(self):
        # check the parsing done by NTPPeers
        ntp = NTPPeers(testdata[1].split("\n"))
        self.assertEqual(ntp.ntpdata['syncpeer'], '202.60.94.11')
        self.assertEqual(ntp.ntpdata['offsetsyncpeer'], 0.259)
        self.assertEqual(ntp.ntpdata['survivors'], 3)
        self.assertEqual(ntp.ntpdata['averageoffsetsurvivors'], 0.21133333333333335)
        self.assertEqual(ntp.ntpdata['discards'], 4)
        self.assertEqual(ntp.ntpdata['averageoffsetdiscards'], 0.768)
        self.assertEqual(ntp.ntpdata['peers'], 7)
        self.assertEqual(ntp.ntpdata['averageoffset'], 0.5294285714285715)
        self.assertEqual(ntp.ntpdata['reachability'], 85.71428571428571)

        # run checks on the data
        check = CheckNTPMon()
        self.assertEqual(check.sync(ntp.ntpdata['syncpeer']), 0, 'Sync peer not detected')
        self.assertEqual(check.offset(ntp.ntpdata['offsetsyncpeer']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetsurvivors']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetdiscards']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffset']), 0, 'Low offset non-OK')
        self.assertEqual(check.peers(ntp.ntpdata['peers']), 0, 'High peers non-OK')
        self.assertEqual(check.reachability(ntp.ntpdata['reachability']), 0,
                         'High reachability non-OK')

        # run overall health checks
        self.assertEqual(ntp.check_sync(), 0, 'Sync peer not detected')
        self.assertEqual(ntp.check_offset(), 0, 'Low offset non-OK')
        self.assertEqual(ntp.check_peers(), 0, 'High peers non-OK')
        self.assertEqual(ntp.check_reachability(), 0, 'High reachability non-OK')

    def test_NTPPeer2(self):
        # check the parsing done by NTPPeers
        ntp = NTPPeers(testdata[2].split("\n"))
        self.assertEqual(ntp.ntpdata['syncpeer'], '91.189.94.4')
        self.assertEqual(ntp.ntpdata['offsetsyncpeer'], 194.54)
        self.assertEqual(ntp.ntpdata['survivors'], 1)
        self.assertEqual(ntp.ntpdata['averageoffsetsurvivors'], 194.54)
        self.assertEqual(ntp.ntpdata['discards'], 0)
        self.assertEqual(ntp.ntpdata.get('averageoffsetdiscards'), None)
        self.assertEqual(ntp.ntpdata['peers'], 1)
        self.assertEqual(ntp.ntpdata['averageoffset'], 194.54)
        self.assertEqual(ntp.ntpdata['reachability'], 100)

        # run checks on the data
        check = CheckNTPMon()
        self.assertEqual(check.sync(ntp.ntpdata['syncpeer']), 0, 'Sync peer not detected')
        self.assertEqual(check.offset(ntp.ntpdata['offsetsyncpeer']), 2, 'High offset non-critical')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetsurvivors']), 2, 'High offset non-critical')
        self.assertEqual(ntp.ntpdata.get('averageoffsetdiscards'), None)
        self.assertEqual(check.offset(ntp.ntpdata['averageoffset']), 2, 'High offset non-critical')
        self.assertEqual(check.peers(ntp.ntpdata['peers']), 2, 'Low peers non-critical')
        self.assertEqual(check.reachability(ntp.ntpdata['reachability']), 0,
                         'High reachability non-OK')

        # run overall health checks
        self.assertEqual(ntp.check_sync(), 0, 'Sync peer not detected')
        self.assertEqual(ntp.check_offset(), 2, 'High offset non-critical')
        self.assertEqual(ntp.check_peers(), 2, 'Low peers non-critical')
        self.assertEqual(ntp.check_reachability(), 0, 'High reachability non-OK')

    def test_NTPPeer3(self):
        # check the parsing done by NTPPeers
        ntp = NTPPeers(testdata[3].split("\n"))
        self.assertEqual(ntp.ntpdata.get('syncpeer'), None)
        self.assertEqual(ntp.ntpdata.get('offsetsyncpeer'), None)
        self.assertEqual(ntp.ntpdata['survivors'], 0)
        self.assertEqual(ntp.ntpdata.get('averageoffsetsurvivors'), None)
        self.assertEqual(ntp.ntpdata['discards'], 8)
        self.assertEqual(ntp.ntpdata['averageoffsetdiscards'], 0.114125)
        self.assertEqual(ntp.ntpdata['peers'], 8)
        self.assertEqual(ntp.ntpdata['averageoffset'], 0.114125)
        self.assertEqual(ntp.ntpdata['reachability'], 4.6875)

        # run checks on the data
        check = CheckNTPMon()
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetdiscards']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffset']), 0, 'Low offset non-OK')
        self.assertEqual(check.peers(ntp.ntpdata['peers']), 0, 'High peers non-OK')
        self.assertEqual(check.reachability(ntp.ntpdata['reachability']), 2,
                         'Low reachability non-critical')

        # run overall health checks
        self.assertEqual(ntp.check_sync(), 2, 'Missing sync peer not detected')
        self.assertEqual(ntp.check_offset(), 1, 'Missing sync peer/survivor offset non-warning')
        self.assertEqual(ntp.check_peers(), 0, 'High peers non-OK')
        self.assertEqual(ntp.check_reachability(), 2, 'Low reachability non-critical')


if __name__ == "__main__":
    unittest.main()

