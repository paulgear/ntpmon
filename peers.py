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

import math
import pprint
import re
import statistics
import sys

from warnings import warn


pp = pprint.PrettyPrinter(width=200)


class NTPPeers(object):

    """
    Parse ntpq -pn output and extract metrics and alerts.
    """

    @staticmethod
    def getmean(l):
        """
        Get the mean of the values in l, or NaN if there is none.
        """
        if len(l) > 0:
            return statistics.mean(l)
        else:
            return float('nan')

    @staticmethod
    def getstdev(l, mean):
        """
        Get the mean of the values in l, or NaN if there is none.
        """
        if len(l) > 0:
            return statistics.pstdev(l, mean)
        else:
            return float('nan')

    @staticmethod
    def rms(l):
        """
        Return the root mean square of the values in the list.
        """
        if len(l) > 0:
            squares = [x ** 2 for x in l]
            return math.sqrt(statistics.mean(squares))
        else:
            return float('nan')

    peertypes = {
        'backup': '#',
        'discard': ' .-x',
        'survivor': '+',
        'syncpeer': '*o',
        'unknown': '',
        'ALL': '',
    }

    @classmethod
    def plural(cls, peertype):
        if peertype in ['ALL', 'syncpeer']:
            return peertype
        else:
            return peertype + 's'

    @classmethod
    def tallytotype(cls, s):
        """
        Convert the given tally code string to a peer type.
        Return 'unknown' if it doesn't match any known tally code.
        """
        for peertype in cls.peertypes:
            if s in cls.peertypes[peertype]:
                return peertype
        return 'unknown'

    noiselines = [
        r'remote\s+refid\s+st\s+t\s+when\s+poll\s+reach\s+',
        r'^=*$',
        r'No association ID.s returned',
    ]

    @classmethod
    def isnoiseline(cls, line):
        """
        Return true if the line is known to be non-interesting.
        """
        for regex in cls.noiselines:
            if re.search(regex, line) is not None:
                return True
        return False

    @classmethod
    def peerline(cls, line):
        """
        Return a list containing the peer type and the 10 peer fields,
        if the line is a correctly-formatted peer line.
        """
        if cls.isnoiseline(line):
            return False

        peertype = cls.tallytotype(line[0])
        if peertype == 'unknown':
            warn('Unknown peer tally code: %s' % line[0])
            return False

        fields = line[1:].split()
        if len(fields) != 10:
            warn('Invalid peer line - there are %d fields: %s' % (len(fields), line))
            return False

        # stratum should be an integer
        try:
            fields[2] = int(fields[2])
        except ValueError:
            warn('Stratum is not an integer: %s' % fields[2])
            return False

        # when should be an integer or '-'
        try:
            if fields[4] != '-':
                fields[4] = int(fields[4])
        except ValueError:
            warn('Last poll time is not an integer: %s' % fields[4])
            return False

        # poll should be an integer
        try:
            fields[5] = int(fields[5])
        except ValueError:
            warn('Poll interval is not an integer: %s' % fields[5])
            return False

        # reachability should be octal
        try:
            # convert to octal
            fields[6] = int(fields[6], 8)
            # convert to binary, count the # of 1s (maximum 8), convert to a percentage
            fields[6] = bin(fields[6]).count("1") * 100 / 8
        except ValueError:
            warn('Reachability is not an octal value: %s' % fields[6])
            return False

        # fields 7-9 should be floats
        for i in range(7, 10):
            try:
                fields[i] = float(fields[i])
            except ValueError:
                warn('Field %d is not numeric: %s' % (i, fields[i]))
                return False

        return [peertype] + fields

    ignorerefids = [
        '.LOCL.',
        '.INIT.',
        '.POOL.',
        '.XFAC.',
    ]

    @classmethod
    def validpeer(cls, peer):
        if not peer:
            return False

        refid = peer[2]
        if refid in cls.ignorerefids:
            return False

        stratum = peer[3]
        if stratum < 0 or stratum > 15:
            return False

        return True

    peerfields = {
        'address': 1,
        'delay': 8,
        'jitter': 10,
        'offset': 9,
        'reach': 7,
        'stratum': 3,
    }

    @classmethod
    def appendpeer(cls, peers, peer):
        """
        Append the fields from the peer record to the equivalent lists in the peer type dict entry.
        """
        peertype = peer[0]
        for f in cls.peerfields:
            peers[peertype][f].append(peer[cls.peerfields[f]])

    @classmethod
    def newpeerdict(cls):
        """
        Create a dict with an empty entry for each peer type and an empty array for each type's metrics.
        """
        peers = {}
        for t in cls.peertypes:
            peers[t] = {}
            for f in cls.peerfields:
                peers[t][f] = []
        return peers

    @classmethod
    def parse(cls, lines):
        """
        Return a dictionary of peers, parsed from the provided lines.
        """
        peers = cls.newpeerdict()
        if isinstance(lines, str):
            lines = lines.split('\n')
        for l in lines:
            peer = cls.peerline(l)
            if peer and cls.validpeer(peer):
                cls.appendpeer(peers, peer)
                # the sync peer is also a survivor
                if peer[0] == 'syncpeer':
                    peer[0] = 'survivor'
                    cls.appendpeer(peers, peer)

                # also append the line to the all peer type
                peer[0] = 'ALL'
                cls.appendpeer(peers, peer)
        return peers

    def getmetrics(self, peers=None):
        """
        Return a set of metrics based on the data in peers.
        If peers is None, use self.peers.
        """
        if peers is None:
            peers = self.peers
        metrics = {}
        for t in NTPPeers.peertypes:
            pt = NTPPeers.plural(t)

            # number of peers of this type
            metrics[pt] = len(peers[t]['address'])

            # offset of peers of this type
            metrics[pt + '-offset-mean'] = NTPPeers.getmean(peers[t]['offset'])
            metrics[pt + '-offset-stdev'] = NTPPeers.getstdev(peers[t]['offset'], metrics[pt + '-offset-mean'])
            metrics[pt + '-offset-rms'] = NTPPeers.rms(peers[t]['offset'])

            # reachability of peers of this type
            metrics[pt + '-reach-mean'] = NTPPeers.getmean(peers[t]['reach'])
            metrics[pt + '-reach-stdev'] = NTPPeers.getstdev(peers[t]['reach'], metrics[pt + '-reach-mean'])
            # The rms of reachability is not very useful, because it's always positive
            # (so it should be very close to the mean), but we include it for completeness.
            metrics[pt + '-reach-rms'] = NTPPeers.rms(peers[t]['reach'])

        return metrics

    def __init__(self, lines):
        self.peers = self.parse(lines)


if __name__ == "__main__":
    p = NTPPeers(sys.stdin.read())
    pp.pprint(p.peers)
    m = p.getmetrics()
    pp.pprint(m)
