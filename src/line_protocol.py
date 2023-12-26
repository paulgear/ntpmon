#
# Copyright:    (c) 2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>


# Line protocol syntax:
# <measurement>[,<tag_key>=<tag_value>[,<tag_key>=<tag_value>]] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]
# Ref: https://docs.influxdata.com/influxdb/v2/reference/syntax/line-protocol/
# With telegraf we can only use timestamps in nanosecond format


exclude_fields = []

exclude_tags = []


def format_tags(metrics: dict, additional_tags: dict) -> str:
    return ",".join(
        [
            f"{transform_identifier(tag)}={metrics[tag]}"
            for tag in sorted(metrics.keys())
            if tag not in exclude_tags and type(metrics[tag]) == str
        ]
        + [
            f"{transform_identifier(tag)}={additional_tags[tag]}"
            for tag in sorted(additional_tags.keys())
            if tag not in exclude_tags
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
    seconds = int(timestamp)
    nanoseconds = int((timestamp - seconds) * 1_000_000_000)
    return (seconds, nanoseconds)


def to_line_protocol(metrics: dict, which: str, additional_tags: dict = {}) -> str:
    if "datetime" in metrics:
        seconds, nanoseconds = timestamp_to_line_protocol(metrics["datetime"].timestamp())
        timestamp = f" {seconds}{nanoseconds:09}"
    else:
        timestamp = ""
    return f"{which},{format_tags(metrics, additional_tags)} {format_fields(metrics)}{timestamp}"


def transform_identifier(id: str) -> str:
    return id.replace("-", "_").strip("_")
