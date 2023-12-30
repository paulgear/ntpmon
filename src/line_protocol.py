#
# Copyright:    (c) 2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>


# Line protocol syntax:
# <measurement>[,<tag_key>=<tag_value>[,<tag_key>=<tag_value>]] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]
# Ref: https://docs.influxdata.com/influxdb/v2/reference/syntax/line-protocol/
# With telegraf we can only use timestamps in nanosecond format


import re


exclude_fields = []

exclude_tags = []


# https://docs.influxdata.com/influxdb/v2/reference/syntax/line-protocol/#special-characters
def escape_tag_value(s: str) -> str:
    return s.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def format_tags(metrics: dict, additional_tags: dict) -> str:
    all_metrics = {}
    all_metrics.update(additional_tags)
    all_metrics.update(metrics)
    return ",".join(
        [
            f"{transform_identifier(tag)}={escape_tag_value(all_metrics[tag])}"
            for tag in sorted(all_metrics.keys())
            if tag not in exclude_tags and type(all_metrics[tag]) == str
        ]
    )


def format_fields(metrics: dict) -> str:
    return ",".join(
        [
            f"{transform_identifier(field)}={metrics[field]}"
            for field in sorted(metrics.keys())
            if field not in exclude_fields and type(metrics[field]) == float
        ]
        + [
            f"{transform_identifier(field)}={metrics[field]}i"
            for field in sorted(metrics.keys())
            if field not in exclude_fields and type(metrics[field]) == int
        ]
        + [
            f"{transform_identifier(field)}={int(metrics[field])}i"
            for field in sorted(metrics.keys())
            if field not in exclude_fields and type(metrics[field]) == bool
        ]
    )


def timestamp_to_line_protocol(timestamp: float) -> (int, int):
    if timestamp < 0:
        raise ValueError("timestamps cannot be negative")
    seconds = int(timestamp)
    nanoseconds = round((timestamp - seconds) * 1_000_000_000)
    return (seconds, nanoseconds)


def to_line_protocol(metrics: dict, which: str, additional_tags: dict = {}) -> str:
    if "datetime" in metrics:
        seconds, nanoseconds = timestamp_to_line_protocol(metrics["datetime"].timestamp())
        timestamp = f" {seconds}{nanoseconds:09}"
    else:
        timestamp = ""
    tags = format_tags(metrics, additional_tags)
    if len(tags):
        tags = "," + tags
    return f"{which}{tags} {format_fields(metrics)}{timestamp}"


punctuation = re.compile(r'[-!@#$%^&()<>,./\?+=:;"\'\[\]\{\}\*\s]+')


def transform_identifier(id: str) -> str:
    return punctuation.sub("_", id).strip("_")
