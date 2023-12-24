#!/usr/bin/python
#
# Copyright:    (c) 2015-2016 Paul D. Gear
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

import argparse
import unittest
import sys

from check_ntpmon import CheckNTPMon, CheckNTPMonSilent, NTPCheck

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

demodata = [
    """
     remote  refid   st t when poll reach   delay   offset    disp
=========================================================================
*WWVB_SPEC(1)  .WWVB.  0 l  114   64  377     0.00   37.623   12.77
 relay.hp.com    listo 2 u  225  512  377     6.93   34.052   10.79
 cosl4.cup.hp.co listo 2 u  226  512  377     4.18   29.385   13.21
 paloalto.cns.hp listo 2 u  235  512  377     9.80   33.487   11.61
 chelmsford.cns. listo 2 u  233  512  377    88.79   30.462    9.66
 atlanta.cns.hp. listo 2 u  231  512  377    67.44   32.909   12.86
 colorado.cns.hp listo 2 u  233  512  377    43.70   30.077   18.63
 boise.cns.hp.co listo 2 u  224  512  377    33.42   31.682    8.54
""",
    """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 GENERIC(1)      .GPS.            0 l    4   64    1    0.000   -0.719   0.001
 PPS(1)          .PPS.           16 l    -   64    0    0.000    0.000 4000.00
 ltgpsdemo       .INIT.          16 u    3   64    0    0.000    0.000 4000.00
""",
    """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 GENERIC(1)      .GPS.            0 l   38   64    7    0.000   -1.193   0.528
 PPS(1)          .PPS.           16 l    -   64    0    0.000    0.000 4000.00
 ltgpsdemo       .GPS.            1 u   33   64    1    0.624   -0.417   0.001
""",
    """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*GENERIC(1)      .GPS.            0 l   45   64  377    0.000   -0.437   0.203
 PPS(1)          .PPS.           16 l    -   64    0    0.000    0.000 4000.00
+ltgpsdemo       .PPS.            1 u  116  512  377    0.500    0.349   0.106
""",
    # mangled from Cisco router demo output:
    """
 27.54.95.11     .STEP.          16 u    -     64     0  0.000   0.000 15937.
+130.102.128.23  216.218.254.20   2 u   25     64    77 51.267  32.537 189.39
 128.184.34.53   169.254.0.1      3 u   64     64   122 49.115  29.474 1939.5
*129.250.35.250  133.243.238.24   2 u   14     64   177 261.47   7.906 65.514
+129.250.35.251  133.243.238.24   2 u   55     64    77 255.70  13.942 190.86
""",
    """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 ff05::101       .MCST.          16 u    -   64    0    0.000    0.000 4000.00
*example.site.co .PPS.            1 u  320 1024  377    1.955   -1.234   1.368
""",
    """
remote refid st t when poll reach delay offset jitter
==========================================================
-navobs1.oar.net .USNO. 1 u 958 1024 377 89.425 -6.073 0.695
*navobs1.gatech. .GPS. 1 u 183 1024 375 82.102 1.639 0.281
-NAVOBS1.MIT.EDU .PSC. 1 u 895 1024 377 90.912 -0.207 0.368
+navobs1.wustl.e .GPS. 1 u 48 1024 377 76.890 1.093 0.525
-bigben.cac.wash .USNO. 1 u 924 1024 377 113.327 0.028 0.326
+tick.ucla.edu .GPS. 1 u 107 1024 377 102.470 2.032 0.482
-ntp.alaska.edu .GPS. 1 u 881 1024 377 168.741 5.180 5.157
-tock.mhpcc.hpc. .GPS. 1 u 933 1024 377 174.518 -1.094 0.054
""",
    """
remote refid st t when poll reach delay offset disp
==========================================================
+128.252.19.1 .GPS. 1 u 495 1024 377 30.90 -6.366 8.26
*139.78.133.139 .USNO. 1 u 936 1024 377 48.43 -2.906 5.20
""",
    """
remote refid st t when poll reach delay offset jitter
======================================================
+navobs1.wustl.e .GPS. 1 u 241 256 377 77.626 1.744 0.195
-tick.ucla.edu .GPS. 1 u 136 256 377 102.069 2.019 2.281
+ntp.alaska.edu .GPS. 1 u 207 256 377 168.971 0.528 6.612
*GPS_NMEA(1) .GPS. 0 l 62 64 377 0.000 0.000 0.001
LOCAL(0) .LOCL. 10 l 62 64 377 0.000 0.000 0.000
""",
    """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*dione.cbane.org 204.123.2.5      2 u  509 1024  377   51.661   -3.343   0.279
+ns1.your-site.c 132.236.56.252   3 u  899 1024  377   48.395    2.047   1.006
+ntp.yoinks.net  129.7.1.66       2 u  930 1024  377    0.693    1.035   0.241
 LOCAL(0)        .LOCL.          10 l   45   64  377    0.000    0.000   0.001
""",
    """
remote refid st t when poll reach delay offset jitter
======================================================================
 6s-ntp .ACST. 16 u - 64 0 0.000 0.000 0.002
*ntp0.kostecke.n 192.168.19.2 3 u 225 1024 377 0.723 -3.463 1.889
""",
    """
     remote refid st t when poll reach delay offset jitter
==============================================================================
 10.35.60.40 .INIT. 16 u 505 1024 0 0.000 0.000 0.000
 10.35.60.41 .INIT. 16 u 471 1024 0 0.000 0.000 0.000
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
        # check the parsing done by NTPCheck
        ntp = NTPCheck(testdata[0].split("\n"))
        self.assertEqual(ntp.ntpdata['syncpeer'], '91.189.89.199')
        self.assertEqual(ntp.ntpdata['offsetsyncpeer'], 0.598)
        self.assertEqual(ntp.ntpdata['survivors'], 1)
        self.assertEqual(ntp.ntpdata['averageoffsetsurvivors'], 0.598)
        self.assertEqual(ntp.ntpdata['discards'], 0)
        self.assertEqual(ntp.ntpdata.get('averageoffsetdiscards'), None)
        self.assertEqual(ntp.ntpdata['peers'], 1)
        self.assertEqual(ntp.ntpdata['averageoffset'], 0.598)
        self.assertEqual(ntp.ntpdata['reachability'], 100)

        # run checks on the data
        check = CheckNTPMon()
        self.assertEqual(check.sync(ntp.ntpdata['syncpeer']), 0, 'Sync peer not detected')
        self.assertEqual(check.offset(ntp.ntpdata['offsetsyncpeer']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetsurvivors']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffset']), 0, 'Low offset non-OK')
        self.assertEqual(check.peers(ntp.ntpdata['peers']), 2, 'Low peers non-critical')
        self.assertEqual(
            check.reachability(ntp.ntpdata['reachability']), 0,
            'High reachability non-OK')

        # run overall health checks
        self.assertEqual(ntp.check_sync(), 0, 'Sync peer not detected')
        self.assertEqual(ntp.check_offset(), 0, 'Low offset non-OK')
        self.assertEqual(ntp.check_peers(), 2, 'Low peers non-critical')
        self.assertEqual(ntp.check_reachability(), 0, 'High reachability non-OK')

    def test_NTPPeer1(self):
        # check the parsing done by NTPCheck
        ntp = NTPCheck(testdata[1].split("\n"))
        self.assertEqual(ntp.ntpdata['syncpeer'], '202.60.94.11')
        self.assertEqual(ntp.ntpdata['offsetsyncpeer'], 0.259)
        self.assertEqual(ntp.ntpdata['survivors'], 3)
        self.assertEqual(ntp.ntpdata['averageoffsetsurvivors'], 0.21133333333333335)
        self.assertEqual(ntp.ntpdata['discards'], 3)
        self.assertEqual(ntp.ntpdata['averageoffsetdiscards'], 1.024)
        self.assertEqual(ntp.ntpdata['peers'], 6)
        self.assertEqual(ntp.ntpdata['averageoffset'], 0.6176666666666667)
        self.assertEqual(ntp.ntpdata['reachability'], 100)

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
        # check the parsing done by NTPCheck
        ntp = NTPCheck(testdata[2].split("\n"))
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
        # check the parsing done by NTPCheck
        ntp = NTPCheck(testdata[3].split("\n"))
        self.assertEqual(ntp.ntpdata.get('syncpeer'), None)
        self.assertEqual(ntp.ntpdata.get('offsetsyncpeer'), None)
        self.assertEqual(ntp.ntpdata['survivors'], 0)
        self.assertEqual(ntp.ntpdata.get('averageoffsetsurvivors'), None)
        self.assertEqual(ntp.ntpdata['discards'], 1)
        self.assertEqual(ntp.ntpdata['averageoffsetdiscards'], 0.913)
        self.assertEqual(ntp.ntpdata['peers'], 1)
        self.assertEqual(ntp.ntpdata['averageoffset'], 0.913)
        self.assertEqual(ntp.ntpdata['reachability'], 37.5)

        # run checks on the data
        check = CheckNTPMon()
        self.assertEqual(check.offset(ntp.ntpdata['averageoffsetdiscards']), 0, 'Low offset non-OK')
        self.assertEqual(check.offset(ntp.ntpdata['averageoffset']), 0, 'Low offset non-OK')
        self.assertEqual(check.peers(ntp.ntpdata['peers']), 2, 'Low peers non-critical')
        self.assertEqual(check.reachability(ntp.ntpdata['reachability']), 2,
                         'Low reachability non-critical')

        # run overall health checks
        self.assertEqual(ntp.check_sync(), 2, 'Missing sync peer not detected')
        self.assertEqual(ntp.check_offset(), 1, 'Missing sync peer/survivor offset non-warning')
        self.assertEqual(ntp.check_peers(), 2, 'Low peers non-critical')
        self.assertEqual(ntp.check_reachability(), 2, 'Low reachability non-critical')

    def test_defaults(self):
        c = CheckNTPMon()
        self.assertEqual(c.warnpeers, 2)
        self.assertEqual(c.okpeers, 4)
        self.assertEqual(c.warnoffset, 10)
        self.assertEqual(c.critoffset, 50)
        self.assertEqual(c.warnreach, 75)
        self.assertEqual(c.critreach, 50)

    def test_non_default(self):
        c = CheckNTPMon(1, 2, 9, 49, 80, 60)
        self.assertEqual(c.warnpeers, 1)
        self.assertEqual(c.okpeers, 2)
        self.assertEqual(c.warnoffset, 9)
        self.assertEqual(c.critoffset, 49)
        self.assertEqual(c.warnreach, 80)
        self.assertEqual(c.critreach, 60)

    def test_clone(self):
        ch = CheckNTPMon()
        self.assertFalse(ch.is_silent())
        c = CheckNTPMonSilent.clone(ch)
        self.assertTrue(c.is_silent())
        self.assertEqual(c.warnpeers, 2)
        self.assertEqual(c.okpeers, 4)
        self.assertEqual(c.warnoffset, 10)
        self.assertEqual(c.critoffset, 50)
        self.assertEqual(c.warnreach, 75)
        self.assertEqual(c.critreach, 50)

    def test_clone_non_default(self):
        ch = CheckNTPMon(1, 2, 9, 49, 80, 60)
        self.assertFalse(ch.is_silent())
        c = CheckNTPMonSilent.clone(ch)
        self.assertTrue(c.is_silent())
        self.assertEqual(c.warnpeers, 1)
        self.assertEqual(c.okpeers, 2)
        self.assertEqual(c.warnoffset, 9)
        self.assertEqual(c.critoffset, 49)
        self.assertEqual(c.warnreach, 80)
        self.assertEqual(c.critreach, 60)

    def test_clone_silent(self):
        """Cloning CheckNTPMonSilent should return itself"""
        cs = CheckNTPMonSilent()
        c = CheckNTPMonSilent.clone(cs)
        self.assertEqual(c, cs)

    def test_clone_inheritance(self):
        """Cloning a child class should work too"""
        class testobject(CheckNTPMonSilent):
            def dump(self):
                pass
        obj = testobject()
        self.assertEqual(obj.warnpeers, 2)
        self.assertEqual(obj.okpeers, 4)
        self.assertEqual(obj.warnoffset, 10)
        self.assertEqual(obj.critoffset, 50)
        self.assertEqual(obj.warnreach, 75)
        self.assertEqual(obj.critreach, 50)
        c = CheckNTPMonSilent.clone(obj)
        self.assertEqual(c.warnpeers, 2)
        self.assertEqual(c.okpeers, 4)
        self.assertEqual(c.warnoffset, 10)
        self.assertEqual(c.critoffset, 50)
        self.assertEqual(c.warnreach, 75)
        self.assertEqual(c.critreach, 50)

    def test_clone_inheritance_non_silent(self):
        """Cloning a non-silent child class should work too"""
        class testobject(CheckNTPMon):
            def dump(self):
                pass
        obj = testobject()
        self.assertEqual(obj.warnpeers, 2)
        self.assertEqual(obj.okpeers, 4)
        self.assertEqual(obj.warnoffset, 10)
        self.assertEqual(obj.critoffset, 50)
        self.assertEqual(obj.warnreach, 75)
        self.assertEqual(obj.critreach, 50)
        c = CheckNTPMonSilent.clone(obj)
        self.assertEqual(c.warnpeers, 2)
        self.assertEqual(c.okpeers, 4)
        self.assertEqual(c.warnoffset, 10)
        self.assertEqual(c.critoffset, 50)
        self.assertEqual(c.warnreach, 75)
        self.assertEqual(c.critreach, 50)

    def test_clone_inheritance_non_silent_made_silent(self):
        """Don't try this at home, kids"""
        class testobject(CheckNTPMon):
            def is_silent(self):
                return True
        obj = testobject()
        c = CheckNTPMonSilent.clone(obj)
        self.assertEqual(c, obj)

    def test_bad_clone(self):
        """Cloning something that's not a CheckNTPMonSilent or CheckNTPMon should raise an AttributeError"""
        class testobject(object):
            pass
        obj = testobject()
        self.assertRaises(AttributeError, CheckNTPMonSilent.clone, obj)

    def test_demos(self):
        """Ensure that demo data is parsed successfully and doesn't produce exceptions or unknown results"""
        for d in demodata:
            ntp = NTPCheck(d.split("\n"))
            ntp.dump()
            methods = [ntp.check_offset, ntp.check_peers, ntp.check_reachability,
                       ntp.check_sync, ntp.checks]
            for method in methods:
                ret = method()
                self.assertIn(
                    ret, [0, 1, 2],
                    "Method %s returned invalid result parsing demo data:\n%s\nTry running with --show-demos." % (method, d))


def demo():
    """Duplicate of test_demos which shows full output"""
    i = 0
    for d in demodata:
        print("Parsing demo data %d: %s" % (i, d))
        ntp = NTPCheck(d.split("\n"))
        i += 1
        ntp.dump()
        methods = [ntp.check_offset, ntp.check_peers, ntp.check_reachability,
                   ntp.check_sync, ntp.checks]
        for method in methods:
            ret = method()
            if ret not in [0, 1, 2]:
                print("Method %s returned invalid result parsing demo data:\n%s" % (method, d))
                sys.exit(3)


if __name__ == "__main__":
    # object to store parsed arguments
    test_checkntpmon = CheckNTPMon()

    # parse command line
    parser = argparse.ArgumentParser(description='NTPmon test class')
    parser.add_argument(
        '--show-demos', action='store_true',
        help='Show demo output.')
    args = parser.parse_args(namespace=test_checkntpmon)
    if test_checkntpmon.show_demos:
        demo()
    else:
        unittest.main()
