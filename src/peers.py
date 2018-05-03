
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
Parse 'ntpq -pn' or 'chronyc -c sources' output and extract metrics.
"""

import math
import re
import statistics
import sys

from warnings import warn


class NTPPeers():

    @staticmethod
    def getmean(l):
        """
        Get the mean of the values in the list, or NaN if there is none.
        """
        if len(l) > 0:
            return statistics.mean(l)
        else:
            return float('nan')

    @staticmethod
    def getstdev(l, mean):
        """
        Get the standard deviation of the values in the list, or NaN if there is none.
        """
        if len(l) > 0:
            return statistics.pstdev(l, mean)
        else:
            return float('nan')

    @staticmethod
    def time2seconds(t):
        """
        Return the number of seconds represented by the time string.
        """
        if t[-1:] == 'y':
            return int(t[:-1]) * 86400 * 365.25
        elif t[-1:] == 'd':
            return int(t[:-1]) * 86400
        elif t[-1:] == 'h':
            return int(t[:-1]) * 3600
        elif t[-1:] == 'm':
            return int(t[:-1]) * 60
        else:
            return int(t)

    @staticmethod
    def rms(l):
        """
        Return the root mean square of the values in the list, or NaN if there is none.
        """
        if len(l) > 0:
            squares = [x ** 2 for x in l]
            return math.sqrt(statistics.mean(squares))
        else:
            return float('nan')

    """
    List of peer types by tally code
    For more information, see:
     - http://www.eecis.udel.edu/~mills/ntp/html/decode.html#peer
     - http://www.eecis.udel.edu/~mills/ntp/html/ntpq.html#pe
     - http://psp2.ntp.org/bin/view/Support/TroubleshootingNTP#Section_9.4.
    """
    peertypes = {
        'invalid': ' ~?',  # includes chrony's two different classifications
        'false': 'x',
        'excess': '.',
        'backup': '#',
        'outlier': '-',
        'survivor': '+',
        'sync': '*',
        'pps': 'o',
        'unknown': '',
        'all': '',
    }

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

    noiselines = (
        r'remote\s+refid\s+st\s+t\s+when\s+poll\s+reach\s+',
        r'^=*$',
        r'No association ID.s returned',
    )

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
            return None

        fields = line.split(',')
        if len(fields) == 10:
            fields = cls.chrony_peerline(fields)
            if fields:
                return cls.validate_peerfields(fields, False)
            else:
                return None

        fields = line[1:].split()
        if len(fields) == 10:
            fields = cls.ntpd_peerline(line[0], fields)
            if fields:
                return cls.validate_peerfields(fields, True)
            else:
                return None

        warn('Unable to parse peer line: %s' % line)
        return None

    @classmethod
    def chrony_peerline(cls, fields):
        """Convert chrony peer line to named fields"""
        return {
            'mode': fields[0],
            'tally': fields[1],
            'address': fields[2],
            'stratum': fields[3],
            'poll_pow2': fields[4],
            'reach': fields[5],
            'when': fields[6],
            'moffset': fields[7],
            'offset': fields[8],
            'error': fields[9],
        }

    ignorerefids = (
        '.INIT.',
        '.LOCL.',
        '.POOL.',
        '.STEP.',
        '.XFAC.',
    )

    @classmethod
    def ntpd_peerline(cls, tally, fields):
        if fields[1] in cls.ignorerefids:
            return False
        return {
            'tally': tally,
            'address': fields[0],
            'refid': fields[1],
            'stratum': fields[2],
            'mode': fields[3],
            'when': fields[4],
            'poll': fields[5],
            'reach': fields[6],
            'delay': fields[7],
            'offset': fields[8],
            'jitter': fields[9],
        }

    @classmethod
    def validate_tally(cls, fields):
        peertype = cls.tallytotype(fields['tally'])
        if peertype == 'unknown':
            warn('Unknown peer tally code: %s' % fields['tally'])
            return False
        else:
            fields['tally'] = peertype
        return True

    @classmethod
    def validate_stratum(cls, fields):
        # stratum should be an integer between 0 & 15
        try:
            fields['stratum'] = int(fields['stratum'])
            if fields['stratum'] < 0 or fields['stratum'] > 15:
                warn('Stratum out of bounds: %s' % fields['stratum'])
                return False
        except ValueError:
            warn('Stratum is not an integer: %s' % fields['stratum'])
            return False
        return True

    @classmethod
    def validate_when(cls, fields):
        # when should be an integer or '-'
        try:
            if fields['when'] != '-':
                fields['when'] = NTPPeers.time2seconds(fields['when'])
        except ValueError:
            warn('Last poll time is not an integer: %s' % fields['when'])
            return False
        return True

    @classmethod
    def validate_poll(cls, fields):
        # poll should be an integer in seconds
        if 'poll_pow2' in fields:
            try:
                fields['poll'] = 2 ** int(fields['poll_pow2'])
            except ValueError:
                warn('Poll interval is not an integer: %s' % fields['poll_pow2'])
                return False
        try:
            fields['poll'] = int(fields['poll'])
        except ValueError:
            warn('Poll interval is not an integer: %s' % fields['poll'])
            return False
        return True

    @classmethod
    def validate_reach(cls, fields):
        # reachability should be octal
        try:
            # convert to octal
            fields['reach'] = int(fields['reach'], 8)
            # convert to binary, count the # of 1s (maximum 8), convert to a percentage
            fields['reach'] = bin(fields['reach']).count('1') * 100 / 8
        except ValueError:
            warn('Reachability is not an octal value: %s' % fields['reach'])
            return False
        return True

    @classmethod
    def validate_floats(cls, fields, convert_to_seconds):
        for i in ['offset', 'moffset', 'delay', 'jitter', 'error']:
            try:
                if i in fields:
                    if convert_to_seconds:
                        fields[i] = float(fields[i]) / 1000.0
                    else:
                        fields[i] = float(fields[i])
                    # TODO: Do we really want to limit to microsecond accuracy?
                    # ISTR this was only here to work around python float limitations in the test suite.
                    fields[i] = round(fields[i], 6)
            except ValueError:
                warn('Field %d is not numeric: %s' % (i, fields[i]))
                return False
        return True

    @classmethod
    def validate_peerfields(cls, fields, convert_to_seconds):
        """Validate the supplied peer fields; if convert_to_seconds is True, convert
        offset, delay, moffset, error, and jitter from milliseconds to seconds."""
        if not cls.validate_tally(fields):
            return None
        if not cls.validate_stratum(fields):
            return None
        if not cls.validate_when(fields):
            return None
        if not cls.validate_poll(fields):
            return None
        if not cls.validate_reach(fields):
            return None
        if not cls.validate_floats(fields, convert_to_seconds):
            return None
        return fields

    peerfields = [
        'address',
        'delay',
        'error',
        'jitter',
        'offset',
        'moffset',
        'reach',
        'stratum',
    ]

    @classmethod
    def appendpeer(cls, peers, peer):
        """
        Append the fields from the peer record to the equivalent lists in the peer type dict entry.
        """
        for f in cls.peerfields:
            if f in peer:
                peers[peer['tally']][f].append(peer[f])

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
            if not peer:
                continue

            cls.appendpeer(peers, peer)
            # the pps peer is also a sync peer
            if peer['tally'] == 'pps':
                peer['tally'] = 'sync'
                cls.appendpeer(peers, peer)

            # the sync & pps peers are also survivors
            if peer['tally'] == 'sync':
                peer['tally'] = 'survivor'
                cls.appendpeer(peers, peer)

            # also append the line to the all peer type
            peer['tally'] = 'all'
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
            # number of peers of this type
            metrics[t] = len(peers[t]['address'])

            # offset of peers of this type
            metrics[t + '-offset-mean'] = NTPPeers.getmean(peers[t]['offset'])
            metrics[t + '-offset-stdev'] = NTPPeers.getstdev(peers[t]['offset'], metrics[t + '-offset-mean'])
            metrics[t + '-offset-rms'] = NTPPeers.rms(peers[t]['offset'])

            # reachability of peers of this type
            metrics[t + '-reach-mean'] = NTPPeers.getmean(peers[t]['reach'])
            metrics[t + '-reach-stdev'] = NTPPeers.getstdev(peers[t]['reach'], metrics[t + '-reach-mean'])
            # The rms of reachability is not very useful, because it's always positive
            # (so it should be very close to the mean), but we include it for completeness.
            metrics[t + '-reach-rms'] = NTPPeers.rms(peers[t]['reach'])

        return metrics

    def syncpeer(self):
        try:
            return self.peers['sync']['address'][0]
        except Exception:
            return None

    def __init__(self, lines, runtime=None):
        self.peers = self.parse(lines)
        self.runtime = runtime


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(width=200)
    stdin = sys.stdin.read()
    p = NTPPeers(stdin)
    pp.pprint(p.peers)
    m = p.getmetrics()
    pp.pprint(m)
