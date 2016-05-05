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

import unittest
from peers import NTPPeers

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
    """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 ntp.ubuntu.com  .POOL.          16 p    -   64    0    0.000    0.000   0.000
 0.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 1.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 2.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 3.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 127.127.1.0     .LOCL.          15 l    -   64    0    0.000    0.000   0.000
+91.189.94.4     193.79.237.14    2 u    5  128  377  340.782    3.735  59.463
+223.252.23.219  202.127.210.36   3 u    8  128  377   31.430  -16.143  74.185
+91.189.89.199   193.79.237.14    2 u    1  128  377  349.389   11.235  53.799
+103.51.68.133   192.189.54.33    3 u    1  128  377   97.565   -2.926  48.353
+150.101.233.118 192.189.54.17    3 u    3  128  377   70.775    7.865  57.820
+202.147.104.60  202.6.131.118    2 u  132  128  377   56.657   -1.715  96.938
*54.252.129.186  202.6.131.118    2 u  205  128  376   46.207   -2.489  57.605
""",
]

noiselines = """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
"""

peerlines = """ ntp.ubuntu.com  .POOL.          16 p    -   64    0    0.000    0.000   0.000
 0.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 1.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 2.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 3.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 127.127.1.0     .LOCL.          15 l    -   64    0    0.000    0.000   0.000
+91.189.94.4     193.79.237.14    2 u    5  128  377  340.782    3.735  59.463
+223.252.23.219  202.127.210.36   3 u    8  128  377   31.430  -16.143  74.185
+91.189.89.199   193.79.237.14    2 u    1  128  377  349.389   11.235  53.799
+103.51.68.133   192.189.54.33    3 u    1  128  377   97.565   -2.926  48.353
+150.101.233.118 192.189.54.17    3 u    3  128  377   70.775    7.865  57.820
+202.147.104.60  202.6.131.118    2 u  132  128  377   56.657   -1.715  96.938
*54.252.129.186  202.6.131.118    2 u  205  128  376   46.207   -2.489  57.605"""

alllines = noiselines + peerlines + '\n'

parsedpeers = {
    'backup': {
        'address': [],
        'delay': [],
        'jitter': [],
        'offset': [],
        'reach': [],
        'stratum': [],
    },
    'discard': {
        'address': [],
        'delay': [],
        'jitter': [],
        'offset': [],
        'reach': [],
        'stratum': [],
    },
    'syncpeer': {
        'address': ['54.252.129.186'],
        'delay': [46.207],
        'jitter': [57.605],
        'offset': [-2.489],
        'reach': [0o376],
        'stratum': [2],
    },
    'survivor': {
        'address': ['91.189.94.4', '223.252.23.219', '91.189.89.199', '103.51.68.133', '150.101.233.118', '202.147.104.60', '54.252.129.186'],
        'delay': [340.782, 31.430, 349.389, 97.565, 70.775, 56.657, 46.207],
        'jitter': [59.463, 74.185, 53.799, 48.353, 57.820, 96.938, 57.605],
        'offset': [3.735, -16.143, 11.235, -2.926, 7.865, -1.715, -2.489],
        'reach': [0o377, 0o377, 0o377, 0o377, 0o377, 0o377, 0o376],
        'stratum': [2, 3, 2, 3, 3, 2, 2],
    },
}


class TestNTPPeers(unittest.TestCase):
    """
    Test NTPPeers
    """

    def test_tallytotype(self):
        for i in '*o':
            self.assertEqual(NTPPeers.tallytotype(i), 'syncpeer')
        for i in '+':
            self.assertEqual(NTPPeers.tallytotype(i), 'survivor')
        for i in '#':
            self.assertEqual(NTPPeers.tallytotype(i), 'backup')
        for i in ' .-x':
            self.assertEqual(NTPPeers.tallytotype(i), 'discard')
        for i in ' .-+ox#*':
            self.assertNotEqual(NTPPeers.tallytotype(i), 'unknown')
        for i in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnpqrstuvwyz~!@$%^&()_':
            self.assertEqual(NTPPeers.tallytotype(i), 'unknown')

    def test_isnoiseline(self):
        for s in noiselines.split('\n'):
            self.assertTrue(NTPPeers.isnoiseline(s))

    def test_isntnoiseline(self):
        for s in peerlines.split('\n'):
            self.assertFalse(NTPPeers.isnoiseline(s))

    def test_filternoiselines(self):
        nonNoiseLines = [x for x in alllines.split('\n') if not NTPPeers.isnoiseline(x)]
        self.assertEqual(nonNoiseLines, peerlines.split('\n'))

    def test_isntvalidpeerline(self):
        for s in noiselines.split('\n'):
            self.assertFalse(NTPPeers.peerline(s))

    def test_peerline(self):
        for s in peerlines.split('\n'):
            self.assertTrue(NTPPeers.peerline(s))

    def test_ignorepeer(self):
        """
        The first 6 peer lines in the test data should be ignored
        """
        for s in peerlines.split('\n')[0:5]:
            self.assertFalse(NTPPeers.validpeer(NTPPeers.peerline(s)))

    def test_dontignorepeer(self):
        """
        The remaining peer lines in the test data shouldn't be ignored
        """
        for s in peerlines.split('\n')[6:]:
            self.assertTrue(NTPPeers.validpeer(NTPPeers.peerline(s)))

    def test_parsepeer(self):
        parsed = NTPPeers.parse(alllines)
        self.assertEqual(parsed, parsedpeers)
        print(parsed)


if __name__ == "__main__":
    unittest.main()
