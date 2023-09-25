#!/usr/bin/env python3

import datetime
import glob
import json
import re
import socket
import sys

from typing import Iterable


sample_measurements = """
2021-12-30 11:28:49 17.253.66.253   N  1 111 111 1111   6  6 0.00 -3.420e-04  1.302e-03  4.121e-06  0.000e+00  1.984e-04 47505373 4B K K
2021-12-30 11:28:49 17.253.66.125   N  1 111 111 1111   6  6 0.00 -2.447e-04  1.109e-03  3.707e-06  0.000e+00  1.373e-04 47505373 4B K K
2021-12-30 11:28:49 150.101.186.50  N  2 111 111 1111   6  6 0.00 -1.287e-04  1.978e-02  4.450e-05  6.714e-04  1.282e-03 AC16FE35 4B K K
2021-12-30 11:28:49 169.254.169.123 N  3 111 111 1111   6  6 0.00 -2.082e-04  2.231e-04  1.276e-06  2.136e-04  2.747e-04 0A2C4A4E 4B K K
2021-12-30 11:28:49 150.101.186.48  N  2 111 111 1111   6  6 0.00 -4.276e-04  1.970e-02  4.405e-05  9.003e-04  6.546e-03 AC16FE35 4B K K
2021-12-30 21:38:41 169.254.169.123 N  3 111 111 1101   8  7 0.01 -1.080e-03  2.430e-03  6.257e-07  2.136e-04  2.594e-04 0A2C4A4E 4B K K
"""

sample_statistics = """
2021-12-30 11:43:02 17.253.66.253    2.762e-05 -2.951e-06  1.331e-05 -3.365e-08  1.262e-07 5.5e-02  13   0   6  0.00
2021-12-30 11:43:03 150.101.186.48   3.384e-04 -3.644e-04  1.994e-04 -8.941e-08  1.459e-06 1.4e-01  15   0   6  0.00
2021-12-30 11:44:06 169.254.169.123  3.312e-05 -1.386e-07  1.886e-05  2.105e-09  1.309e-07 3.0e-03  16   0  10  0.00
2021-12-30 11:44:06 150.101.186.50   2.934e-04 -2.109e-04  1.614e-04  2.291e-07  1.257e-06 2.2e-01  14   1   6  0.00
2021-12-30 11:44:07 17.253.66.125    2.984e-05  1.857e-05  1.568e-05  2.843e-08  1.057e-07 1.8e-01  17   0   8  0.00
2021-12-30 11:44:07 17.253.66.253    2.679e-05 -5.997e-06  1.299e-05 -3.711e-08  1.103e-07 1.3e-02  14   0   7  0.00
"""

leapcodes = {
    'N': 0,
    '+': 1,
    '-': 2,
    '?': 3,
}

timestamp_sources = {
    'D': 'daemon',
    'H': 'hardware',
    'K': 'kernel',
}


def checkfail(test: str) -> int:
    """Reverse the polarity of the tests so that 1 asserts the error.
    This is to make it more natural to write queries asserting, e.g. that a packet is a duplicate."""
    return 1 if test == '0' else 0


def refstr(s: str) -> str:
    """Convert from hex string to a printable string (if all characters are printable), or an IP
    address string otherwise.  See https://stackoverflow.com/a/2198052/1621180 for inspiration."""
    packed = bytes.fromhex(s)
    all_printable = [x >= 20 and x <= 126 for x in packed]
    if all(all_printable):
        return ''.join([chr(x) for x in packed])
    else:
        return socket.inet_ntoa(packed)


integer_fields = [
    # 'auth-fail',
    # 'bad-header',
    # 'bogus',
    # 'duplicate',
    # 'exceeded-max-delay',
    # 'exceeded-max-delay-dev-ratio',
    # 'exceeded-max-delay-ratio',
    # 'invalid',
    # 'leap',
    # 'local-poll',
    # 'remote-poll',
    # 'sync-loop',
    # 'synchronized',
    'num-combined',
    'stratum',
]

float_fields = [
    'delay',
    'dispersion',
    'freq',
    'max-error',
    'offset',
    'remaining-correction',
    'root-delay',
    'root-dispersion',
    'score',
    'skew',
    'stdev',
]

tag_fields = [
    'source',
    'refid',
    # 'refstr',
]

exclude_tags = [
    'after',
    'before',
]


skiplines = r'^===|^ *Date'
regex = re.compile(skiplines)


# From chrony.conf measurements.log docs:
# The columns are as follows (the quantities in square brackets are the values from the example line above):
# 1. Date [2015-10-13]
# 2. Hour:Minute:Second. Note that the date-time pair is expressed in UTC, not the local time zone. [05:40:50]
# 3. IP address of server or peer from which measurement came [203.0.113.15]
# 4. Leap status (N means normal, + means that the last minute of the current month has 61 seconds, - means that the last minute of the month has 59 seconds,
#    ? means the remote computer is not currently synchronised.) [N]
# 5. Stratum of remote computer. [2]
# 6. RFC 5905 tests 1 through 3 (1=pass, 0=fail) [111]
# 7. RFC 5905 tests 5 through 7 (1=pass, 0=fail) [111]
# 8. Tests for maximum delay, maximum delay ratio and maximum delay dev ratio, against defined parameters, and a test for synchronisation loop (1=pass, 0=fail) [1111]
# 9. Local poll [10]
# 10. Remote poll [10]
# 11. ‘Score’ (an internal score within each polling level used to decide when to increase or decrease the polling level. This is adjusted based on number of measurements currently
#     being used for the regression algorithm). [1.0]
# 12. The estimated local clock error (theta in RFC 5905). Positive indicates that the local clock is slow of the remote source. [-4.966e-03]
# 13. The peer delay (delta in RFC 5905). [2.296e-01]
# 14. The peer dispersion (epsilon in RFC 5905). [1.577e-05]
# 15. The root delay (DELTA in RFC 5905). [1.615e-01]
# 16. The root dispersion (EPSILON in RFC 5905). [7.446e-03]
# 17. Reference ID of the server’s source as a hexadecimal number. [CB00717B]
# 18. NTP mode of the received packet (1=active peer, 2=passive peer, 4=server, B=basic, I=interleaved). [4B]
# 19. Source of the local transmit timestamp (D=daemon, K=kernel, H=hardware). [D]
# 20. Source of the local receive timestamp (D=daemon, K=kernel, H=hardware). [K]

def parse_measurement(line: str) -> dict:
    f = line.split()
    return {
        # sort by field position rather than name
        'datetime': datetime.datetime.fromisoformat('+'.join((f[0], f[1], '00:00'))),
        'source': f[2],
        'leap': leapcodes[f[3]],
        'stratum': int(f[4]),
        'duplicate': checkfail(f[5][0]),
        'bogus': checkfail(f[5][1]),
        'invalid': checkfail(f[5][2]),
        'auth-fail': checkfail(f[6][0]),
        'synchronized': int(f[6][1]),
        'bad-header': checkfail(f[6][2]),
        'exceeded-max-delay': checkfail(f[7][0]),
        'exceeded-max-delay-ratio': checkfail(f[7][1]),
        'exceeded-max-delay-dev-ratio': checkfail(f[7][2]),
        'sync-loop': checkfail(f[7][3]),
        'local-poll': int(f[8]),
        'remote-poll': int(f[9]),
        'score': float(f[10]),
        'offset': float(f[11]),
        'delay': float(f[12]),
        'dispersion': float(f[13]),
        'root-delay': float(f[14]),
        'root-dispersion': float(f[15]),
        'refid': refstr(f[16]),
        # Leaving the remaining fields out because they're all the same in my experiment, and I don't want to increase tag cardinality unnecessarily.
        # 'refstr': f[16],
        # 'mode': int(f[17][0]),
        # 'interleaved': 1 if f[17][1] == 'I' else 0,
        # 'tx-timestamp': timestamp_sources[f[18]],
        # 'rx-timestamp': timestamp_sources[f[19]],
    }


# Chrony statistics docs
# 1. Date [2015-07-22]
# 2. Hour:Minute:Second. Note that the date-time pair is expressed in UTC, not the local time zone. [05:40:50]
# 3. IP address of server or peer from which measurement comes [203.0.113.15]
# 4. The estimated standard deviation of the measurements from the source (in seconds). [6.261e-03]
# 5. The estimated offset of the source (in seconds, positive means the local clock is estimated to be fast, in this case). [-3.247e-03]
# 6. The estimated standard deviation of the offset estimate (in seconds). [2.220e-03]
# 7. The estimated rate at which the local clock is gaining or losing time relative to the source (in seconds per second, positive means the local clock is gaining). This is relative to
#     the compensation currently being applied to the local clock, not to the local clock without any compensation. [1.874e-06]
# 8. The estimated error in the rate value (in seconds per second). [1.080e-06].
# 9. The ratio of |old_rate - new_rate| / old_rate_error. Large values indicate the statistics are not modelling the source very well. [7.8e-02]
# 10. The number of measurements currently being used for the regression algorithm. [16]
# 11. The new starting index (the oldest sample has index 0; this is the method used to prune old samples when it no longer looks like the measurements fit a linear model). [0, i.e. no
#     samples discarded this time]
# 12. The number of runs. The number of runs of regression residuals with the same sign is computed. If this is too small it indicates that the measurements are no longer represented
#     well by a linear model and that some older samples need to be discarded. The number of runs for the data that is being retained is tabulated. Values of approximately half the
#     number of samples are expected. [8]
# 13. The estimated or configured asymmetry of network jitter on the path to the source which was used to correct the measured offsets. The asymmetry can be between -0.5 and +0.5. A
#     negative value means the delay of packets sent to the source is more variable than the delay of packets sent from the source back. [0.00, i.e. no correction for asymmetry]

def parse_statistics(line: str) -> dict:
    f = line.split()
    return {
        # sort by field position rather than name
        'datetime': datetime.datetime.fromisoformat('+'.join((f[0], f[1], '00:00'))),
        'source': f[2],
        'stdev': float(f[3]),
        'offset': float(f[4]),
        'stdev-est': float(f[5]),
        'skew': float(f[6]),
        'freq': float(f[7]),
        'stress': float(f[8]),
        'samples': int(f[9]),
        'begin-sample': int(f[10]),
        'runs': int(f[11]),
        'asymmetry': float(f[12]),
    }


# Chrony tracking docs:
# 1. Date [2017-08-22]
# 2. Hour:Minute:Second. Note that the date-time pair is expressed in UTC, not the local time zone. [13:22:36]
# 3. The IP address of the server or peer to which the local system is synchronised. [203.0.113.15]
# 4. The stratum of the local system. [2]
# 5. The local system frequency (in ppm, positive means the local system runs fast of UTC). [-3.541]
# 6. The error bounds on the frequency (in ppm). [0.075]
# 7. The estimated local offset at the epoch, which is normally corrected by slewing the local clock (in seconds, positive indicates the clock is fast of UTC). [-8.621e-06]
# 8. Leap status (N means normal, + means that the last minute of this month has 61 seconds, - means that the last minute of the month has 59 seconds, ? means the clock is not currently
#     synchronised.) [N]
# 9. The number of combined sources. [2]
# 10. The estimated standard deviation of the combined offset (in seconds). [2.940e-03]
# 11. The remaining offset correction from the previous update (in seconds, positive means the system clock is slow of UTC). [-2.084e-04]
# 12. The total of the network path delays to the reference clock to which the local clock is ultimately synchronised (in seconds). [1.534e-02]
# 13. The total dispersion accumulated through all the servers back to the reference clock to which the local clock is ultimately synchronised (in seconds). [3.472e-04]
# 14. The maximum estimated error of the system clock in the interval since the previous update (in seconds). It includes the offset, remaining offset correction, root delay, and
#     dispersion from the previous update with the dispersion which accumulated in the interval. [8.304e-03]

#    Date (UTC) Time     IP Address   St   Freq ppm   Skew ppm     Offset L Co  Offset sd Rem. corr. Root delay Root disp. Max. error

def parse_tracking(line: str) -> dict:
    f = line.split()
    return {
        # sort by field position rather than name
        'datetime': datetime.datetime.fromisoformat('+'.join((f[0], f[1], '00:00'))),
        'source': f[2],
        'stratum': int(f[3]),
        'freq': float(f[4]),
        'skew': float(f[5]),
        'offset': float(f[6]),
        'leap': leapcodes[f[7]],
        'num-combined': int(f[8]),
        'stdev': float(f[9]),
        'remaining-correction': float(f[10]),
        'root-delay': float(f[11]),
        'root-dispersion': float(f[12]),
        'max-error': float(f[13]),
    }


# Line protocol syntax:
# <measurement>[,<tag_key>=<tag_value>[,<tag_key>=<tag_value>]] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]

def validate_identifier(id: str) -> str:
    return id.replace('-', '_').strip('_')


def format_tags(metric: dict, additional_tags: dict) -> str:
    return ','.join([
        f'{validate_identifier(tag)}={metric[tag]}' for tag in tag_fields if tag in metric
    ] + [
        f'{validate_identifier(tag)}={additional_tags[tag]}' for tag in additional_tags if tag not in exclude_tags
    ])


def format_fields(metrics: dict) -> str:
    return ','.join([
        f'{validate_identifier(field)}={metrics[field]}' for field in float_fields if field in metrics
    ] + [
        f'{validate_identifier(field)}={metrics[field]}i' for field in integer_fields if field in metrics
    ])


def to_line_protocol(metrics: dict, which: str, additional_tags: dict = {}) -> str:
    timestamp = int(metrics['datetime'].timestamp())
    if 'after' in additional_tags and timestamp < additional_tags['after']:
        return ''
    elif 'before' in additional_tags and timestamp > additional_tags['before']:
        return ''
    else:
        return f'{which},{format_tags(metrics, additional_tags)} {format_fields(metrics)} {timestamp}\n'


def generate_measurement_lines(tags: dict) -> Iterable[str]:
    for filename in glob.glob(f'{tags["ip"]}/var/log/chrony/measurements.log*'):
        with open(filename) as f:
            for s in f.readlines():
                if regex.match(s):
                    continue
                if len(s):
                    yield to_line_protocol(parse_measurement(s), 'measurement', additional_tags=tags)


def generate_statistics_lines(tags: dict) -> Iterable[str]:
    for filename in glob.glob(f'{tags["ip"]}/var/log/chrony/statistics.log*'):
        with open(filename) as f:
            for s in f.readlines():
                if regex.match(s):
                    continue
                if len(s):
                    yield to_line_protocol(parse_statistics(s), 'statistics', additional_tags=tags)


def generate_tracking_lines(tags: dict) -> Iterable[str]:
    for filename in glob.glob(f'{tags["ip"]}/var/log/chrony/tracking.log*'):
        with open(filename) as f:
            for s in f.readlines():
                if regex.match(s):
                    continue
                if len(s):
                    yield to_line_protocol(parse_tracking(s), 'tracking', additional_tags=tags)


def read_hosts(filename: str) -> dict:
    with open(filename) as f:
        return json.load(f)


def write_host_file(which: str, lines: Iterable[str], tags: dict) -> None:
    with open(f'{tags["ip"]}/{which}.line', 'w') as f:
        f.writelines(lines)


def host_to_tags(cloud: str, host: str, attributes: dict) -> dict:
    tags = {
        'cloud': cloud,
        'hostname': host,
    }
    tags.update(attributes)

    if cloud == 'azure':
        tags['az'] = 'aus-east-' + tags['az']

    if tags.get('ipv6') is not None:
        tags['protocol'] = 'ipv6'
        tags['ip'] = tags['ipv6']
        del(tags['ipv6'])
    else:
        tags['protocol'] = 'ipv4'

    return tags


def main():
    clouds = read_hosts(sys.argv[1])
    for c in clouds:
        for h in clouds[c]:
            tags = host_to_tags(c, h, clouds[c][h])
            print(
                tags['cloud'],
                tags['hostname'],
                f"BEFORE: {tags['before']}" if 'before' in tags else f"AFTER: {tags['after']}" if 'after' in tags else 'ALL',
                tags['az'],
                tags['ip']
            )
            write_host_file('measurements', generate_measurement_lines(tags), tags)
            write_host_file('statistics', generate_statistics_lines(tags), tags)
            write_host_file('tracking', generate_tracking_lines(tags), tags)


main()
