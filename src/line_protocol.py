
#
# Copyright:    (c) 2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>


# Line protocol syntax:
# <measurement>[,<tag_key>=<tag_value>[,<tag_key>=<tag_value>]] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]
# Ref: https://docs.influxdata.com/influxdb/v2/reference/syntax/line-protocol/
# With telegraf we can only use timestamps in nanosecond format

import socket


integer_fields = [
    'auth-fail',
    'bad-header',
    'bogus',
    'duplicate',
    'exceeded-max-delay',
    'exceeded-max-delay-dev-ratio',
    'exceeded-max-delay-ratio',
    'invalid',
    'interleaved',
    'leap',
    'local-poll',
    'num-combined',
    'remote-poll',
    'stratum',
    'sync-loop',
    'synchronized',
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
    'mode',
    'refid',
    'rx-timestamp',
    'source',
    'tx-timestamp',
    'type',
]

exclude_tags = [
]


def refstr(s: str) -> str:
    """Convert from hex string to a printable string (if all characters are printable), or an IP
    address string otherwise.  See https://stackoverflow.com/a/2198052/1621180 for inspiration."""
    packed = bytes.fromhex(s)
    all_printable = [x >= 20 and x <= 126 for x in packed]
    if all(all_printable):
        return ''.join([chr(x) for x in packed])
    else:
        return socket.inet_ntoa(packed)


def format_tags(metric: dict, additional_tags: dict) -> str:
    return ','.join([
        f'{transform_identifier(tag)}={metric[tag]}' for tag in tag_fields if tag in metric
    ] + [
        f'{transform_identifier(tag)}={additional_tags[tag]}' for tag in additional_tags if tag not in exclude_tags
    ])


def format_fields(metrics: dict) -> str:
    return ','.join([
        f'{transform_identifier(field)}={metrics[field]}' for field in float_fields if field in metrics
    ] + [
        f'{transform_identifier(field)}={metrics[field]}i' for field in integer_fields if field in metrics
    ])


def timestamp_to_line_protocol(timestamp: float) -> (int, int):
    seconds = int(timestamp)
    nanoseconds = int((timestamp - seconds) * 1_000_000_000)
    return (seconds, nanoseconds)


def to_line_protocol(metrics: dict, which: str, additional_tags: dict = {}) -> str:
    seconds, nanoseconds = timestamp_to_line_protocol(metrics['datetime'].timestamp())
    return f'{which},{format_tags(metrics, additional_tags)} {format_fields(metrics)} {seconds}{nanoseconds:09}'


def transform_identifier(id: str) -> str:
    return id.replace('-', '_').strip('_')
