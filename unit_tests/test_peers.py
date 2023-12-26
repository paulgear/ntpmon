#!/usr/bin/env python3
#
# Copyright:    (c) 2016-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import math
import unittest

from peers import NTPPeers

testdata = {
    # 'ntpq -np' output
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
""": 1,
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
""": 6,
    """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*91.189.94.4     131.188.3.220    2 u  338 1024  377    1.600  -194.54 171.548
""": 1,
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
""": 1,
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
""": 7,
    # 'chronyc -c sources' output
    """
^,-,103.35.80.142,2,10,377,61,-0.004040866,-0.004040866,0.198811710
^,-,150.101.178.79,2,10,377,615,-0.001099222,-0.001058915,0.185534596
^,-,212.71.244.243,3,6,377,57,0.031961128,0.031961128,0.067624234
^,-,213.130.44.252,2,10,377,828,0.000489526,0.000529030,0.024700930
^,-,46.227.203.3,2,10,377,632,0.001439559,0.001479800,0.038919181
^,-,188.114.116.1,2,10,377,135,0.000449052,0.000449052,0.027969483
^,-,87.124.126.49,2,10,377,827,-0.003650273,-0.003610766,0.034486122
^,-,178.79.160.57,2,9,377,276,-0.000089910,-0.000048331,0.009740895
^,-,195.195.221.100,1,10,377,159,-0.000166417,-0.000166417,0.006248965
^,-,213.251.53.217,2,10,377,663,-0.000198662,-0.000158539,0.034089874
^,-,109.123.121.128,3,10,377,115,-0.000219732,-0.000219732,0.040166985
^,-,134.0.16.1,2,10,377,984,0.000182785,0.000221703,0.033773787
^,-,139.162.250.196,2,9,377,504,0.001067959,0.001108684,0.014812219
^,*,85.199.214.102,1,10,377,252,0.000006879,0.000048551,0.001954214
^,+,85.199.214.98,1,10,377,27,0.000085761,0.000085761,0.002132857
^,-,176.58.109.199,2,9,377,226,-0.001007187,-0.001007187,0.051315147
^,-,195.219.205.9,2,10,377,502,0.000891129,0.000931858,0.075150654
^,-,217.114.59.3,2,10,377,586,0.000159914,0.000200329,0.044174805
^,-,91.189.94.4,2,10,377,647,-0.000059134,-0.000018948,0.026894709
^,-,91.189.91.157,2,10,377,381,-0.000194028,-0.000152841,0.075035207
^,-,91.189.89.199,2,9,377,129,-0.000376504,-0.000376504,0.058679685
^,-,91.189.89.198,2,10,377,713,-0.000519517,-0.000479578,0.046003979
""": 22,
    """
^,-,91.189.89.198,2,6,77,11,-0.000482684,-0.000482684,0.027948668
^,-,91.189.89.199,2,6,77,12,-0.000561509,-0.000647144,0.031918235
^,-,91.189.91.157,2,6,77,11,-0.000204331,-0.000204331,0.079648107
^,-,91.189.94.4,2,6,77,11,-0.000073629,-0.000073629,0.039985429
^,-,178.79.155.116,2,6,77,11,-0.002347225,-0.002347225,0.049551181
^,-,178.62.235.154,3,6,77,13,-0.001039979,-0.001125386,0.040236827
^,-,162.213.35.121,2,6,77,14,-0.000656518,-0.000741345,0.033012766
^,*,194.80.204.184,1,6,77,12,-0.000018392,-0.000104350,0.006169558
""": 8,
    # We can even mix both
    """
 127.127.1.0     .LOCL.          15 l    -   64    0    0.000    0.000   0.000
 3.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
*54.252.129.186  202.6.131.118    2 u  205  128  376   46.207   -2.489  57.605
^,-,91.189.89.198,2,6,77,11,-0.000482684,-0.000482684,0.027948668
 91.189.89.199   192.93.2.20      2 u   21   64    7  336.631    0.913   0.223
^,-,91.189.91.157,2,6,77,11,-0.000204331,-0.000204331,0.079648107
^,-,91.189.94.4,2,10,377,647,-0.000059134,-0.000018948,0.026894709
""": 5,
    # some made-up values to test time2seconds
    """
 127.127.1.0     .LOCL.          15 l    -   64    0    0.000    0.000   0.000
+91.189.94.4     193.79.237.14    2 u   5m  128  300  340.782    3.735  59.463
+223.252.23.219  202.127.210.36   3 u   8h  128  301   31.430  -16.143  74.185
+91.189.89.199   193.79.237.14    2 u   2d  128  302  349.389   11.235  53.799
+103.51.68.133   192.189.54.33    3 u   1y  128  303   97.565   -2.926  48.353
+150.101.233.118 192.189.54.17    3 u    3  128  304   70.775    7.865  57.820
+202.147.104.60  202.6.131.118    2 u  132  128  305   56.657   -1.715  96.938
*54.252.129.186  202.6.131.118    2 u  205  128  306   46.207   -2.489  57.605
""": 7,
}

noiselines = """     remote           refid      st t when poll reach   delay   offset  jitter
=============================================================================="""

inactivepeerlines = """ ntp.ubuntu.com  .POOL.          16 p    -   64    0    0.000    0.000   0.000
 0.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 1.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 2.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 3.au.pool.ntp.o .POOL.          16 p    -   64    0    0.000    0.000   0.000
 127.127.1.0     .LOCL.          15 l    -   64    0    0.000    0.000   0.000"""

peerlines = """+91.189.94.4     193.79.237.14    2 u    5  128  377  340.782    3.735  59.463
+223.252.23.219  202.127.210.36   3 u    8  128  377   31.430  -16.143  74.185
+91.189.89.199   193.79.237.14    2 u    1  128  377  349.389   11.235  53.799
+103.51.68.133   192.189.54.33    3 u    1  128  377   97.565   -2.926  48.353
+150.101.233.118 192.189.54.17    3 u    3  128  377   70.775    7.865  57.820
+202.147.104.60  202.6.131.118    2 u  132  128  377   56.657   -1.715  96.938
*54.252.129.186  202.6.131.118    2 u  205  128  376   46.207   -2.489  57.605"""

alllines = noiselines + "\n" + inactivepeerlines + "\n" + peerlines + "\n"

parsedpeers = {
    "backup": {
        "address": [],
        "delay": [],
        "error": [],
        "jitter": [],
        "moffset": [],
        "offset": [],
        "reach": [],
        "stratum": [],
    },
    "excess": {
        "address": [],
        "delay": [],
        "error": [],
        "jitter": [],
        "moffset": [],
        "offset": [],
        "reach": [],
        "stratum": [],
    },
    "false": {
        "address": [],
        "delay": [],
        "error": [],
        "jitter": [],
        "moffset": [],
        "offset": [],
        "reach": [],
        "stratum": [],
    },
    "invalid": {
        "address": [],
        "delay": [],
        "error": [],
        "jitter": [],
        "moffset": [],
        "offset": [],
        "reach": [],
        "stratum": [],
    },
    "outlier": {
        "address": [],
        "delay": [],
        "error": [],
        "jitter": [],
        "moffset": [],
        "offset": [],
        "reach": [],
        "stratum": [],
    },
    "pps": {
        "address": [],
        "delay": [],
        "error": [],
        "jitter": [],
        "moffset": [],
        "offset": [],
        "reach": [],
        "stratum": [],
    },
    "sync": {
        "address": ["54.252.129.186"],
        "delay": [0.046207],
        "error": [],
        "jitter": [0.057605],
        "moffset": [],
        "offset": [-0.002489],
        "reach": [87.5],
        "stratum": [2],
    },
    "survivor": {
        "address": [
            "91.189.94.4",
            "223.252.23.219",
            "91.189.89.199",
            "103.51.68.133",
            "150.101.233.118",
            "202.147.104.60",
            "54.252.129.186",
        ],
        "delay": [0.340782, 0.031430, 0.349389, 0.097565, 0.070775, 0.056657, 0.046207],
        "error": [],
        "jitter": [0.059463, 0.074185, 0.053799, 0.048353, 0.057820, 0.096938, 0.057605],
        "moffset": [],
        "offset": [0.003735, -0.016143, 0.011235, -0.002926, 0.007865, -0.001715, -0.002489],
        "reach": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 87.5],
        "stratum": [2, 3, 2, 3, 3, 2, 2],
    },
    "unknown": {
        "address": [],
        "delay": [],
        "error": [],
        "jitter": [],
        "moffset": [],
        "offset": [],
        "reach": [],
        "stratum": [],
    },
    "all": {
        "address": [
            "91.189.94.4",
            "223.252.23.219",
            "91.189.89.199",
            "103.51.68.133",
            "150.101.233.118",
            "202.147.104.60",
            "54.252.129.186",
        ],
        "delay": [0.340782, 0.031430, 0.349389, 0.097565, 0.070775, 0.056657, 0.046207],
        "error": [],
        "jitter": [0.059463, 0.074185, 0.053799, 0.048353, 0.057820, 0.096938, 0.057605],
        "moffset": [],
        "offset": [0.003735, -0.016143, 0.011235, -0.002926, 0.007865, -0.001715, -0.002489],
        "reach": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 87.5],
        "stratum": [2, 3, 2, 3, 3, 2, 2],
    },
}


class TestNTPPeers(unittest.TestCase):
    """
    Test NTPPeers
    """

    def setUp(self):
        self.maxDiff = None

    codes = {
        "#": "backup",
        ".": "excess",
        "~": "invalid",
        " ": "invalid",
        "?": "invalid",
        "o": "pps",
        "-": "outlier",
        "+": "survivor",
        "*": "sync",
        "x": "false",
    }

    def test_tallytotype_known(self):
        """Ensure known codes are valid tally types and that they correctly match their type."""
        for t in TestNTPPeers.codes:
            self.assertEqual(NTPPeers.tallytotype(t), TestNTPPeers.codes[t])

    def test_tallytotype_unknown(self):
        """Ensure most printables are not valid tally types."""
        for t in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnpqrstuvwyz!@$%^&()_=[]{}|:;\"<>,/\\'":
            self.assertEqual(NTPPeers.tallytotype(t), "unknown")

    def test_isnoiseline(self):
        """Ensure noise lines are classified as such."""
        for s in noiselines.split("\n"):
            self.assertTrue(NTPPeers.isnoiseline(s))

    def test_inactivepeerisntnoise(self):
        """Ensure inactive peer lines aren't classified as noise."""
        for s in inactivepeerlines.split("\n"):
            self.assertFalse(NTPPeers.isnoiseline(s))

    def test_peerisntnoise(self):
        """Ensure valid peer lines aren't classified as noise."""
        for s in peerlines.split("\n"):
            self.assertFalse(NTPPeers.isnoiseline(s))

    def test_filternoiselines(self):
        """Compare the output of alllines filtered by isnoiseline() with the known non-noise lines."""
        nonNoiseLines = [x for x in alllines.split("\n") if not NTPPeers.isnoiseline(x)]
        self.assertEqual(nonNoiseLines, inactivepeerlines.split("\n") + peerlines.split("\n"))

    def test_isntvalidpeerline(self):
        """Ensure the known noise lines aren't valid peer lines."""
        for s in noiselines.split("\n"):
            self.assertIsNone(NTPPeers.peerline(s))

    def test_inactivepeerline(self):
        """Ensure the inactive peer lines aren't valid peer lines."""
        for s in inactivepeerlines.split("\n"):
            self.assertIsNone(NTPPeers.peerline(s))

    def test_peerline(self):
        """Ensure the known peer lines are valid peer lines."""
        for s in peerlines.split("\n"):
            self.assertIsNotNone(NTPPeers.peerline(s))

    def test_noparsepeer(self):
        """Ensure the result of parsed noise lines is empty."""
        parsed = NTPPeers.parse(noiselines)
        empty = NTPPeers.newpeerdict()
        self.assertEqual(parsed, empty)

    def test_noparsestratum99(self):
        """Ensure the result of parsed incorrect peer line is empty."""
        empty = NTPPeers.newpeerdict()
        parsed = NTPPeers.parse(" 1234 5678 99 u 8 128 377 31.430  -16.143  74.185")
        self.assertEqual(parsed, empty)

    def test_parsepeer(self):
        """Ensure the parsed peer lines matches the expected values."""
        parsed = NTPPeers.parse(alllines)
        self.assertEqual(parsed, parsedpeers)

    def test_getmetrics(self):
        """Ensure the sync metric for parsed peer lines matches the expected values."""
        p = NTPPeers(alllines)
        metrics = p.getmetrics()
        self.assertEqual(metrics["sync"], 1)

    def test_parsetestdata(self):
        """Ensure the test data matches the expected number of valid peers."""
        for t in testdata:
            parsed = NTPPeers.parse(t)
            self.assertEqual(len(parsed["all"]["address"]), testdata[t])

    def test_rootmeansquare(self):
        """Test root mean square function."""
        self.assertTrue(math.isnan(NTPPeers.rms([])))
        self.assertEqual(NTPPeers.rms([3]), 3)
        self.assertEqual(NTPPeers.rms([3, 4]), math.sqrt((9 + 16) / 2))
        self.assertEqual(NTPPeers.rms([3, 4, 5]), math.sqrt((9 + 16 + 25) / 3))
        self.assertEqual(NTPPeers.rms([3, 4, 5, 6]), math.sqrt((9 + 16 + 25 + 36) / 4))

    """
    FIXME: Need individual test coverage:
    def time2seconds(t):
    def validate_tally(cls, fields):
    def validate_stratum(cls, fields):
    def validate_when(cls, fields):
    def validate_poll(cls, fields):
    def validate_reach(cls, fields):
    def validate_floats(cls, fields, convert_to_seconds):
    def validate_peerfields(cls, fields, convert_to_seconds):
    def appendpeer(cls, peers, peer):
    def newpeerdict(cls):
    def syncpeer(self):
    """


if __name__ == "__main__":
    unittest.main()
