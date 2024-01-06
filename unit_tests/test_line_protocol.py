#
# Copyright:    (c) 2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import time
import pytest

import line_protocol


def test_escape_tag_value() -> None:
    assert line_protocol.escape_tag_value("hello=world") == "hello\\=world"
    assert line_protocol.escape_tag_value("hello world") == "hello\\ world"
    assert line_protocol.escape_tag_value("hello, world") == "hello\\,\\ world"


def test_timestamp_to_line_protocol() -> None:
    assert line_protocol.timestamp_to_line_protocol(1) == (1, 0)
    assert line_protocol.timestamp_to_line_protocol(1.123_456_789) == (1, 123_456_789)
    assert line_protocol.timestamp_to_line_protocol(1.9) == (1, 900_000_000)
    assert line_protocol.timestamp_to_line_protocol(1.999) == (1, 999_000_000)
    assert line_protocol.timestamp_to_line_protocol(1.999_999) == (1, 999_999_000)
    assert line_protocol.timestamp_to_line_protocol(1.999_999_999) == (1, 999_999_999)
    with pytest.raises(ValueError):
        # We should never get to either of these assert statements - the
        # ValueError should be raised first.
        assert line_protocol.timestamp_to_line_protocol(-1) == (-1, 0)
        assert False


def test_to_line_protocol() -> None:
    now_ns = time.time_ns()
    metrics = {
        "associd": 0,
        "timestamp_ns": now_ns,
        "frequency": -11.673,
        "leap": False,
        "offset": +0.0000145826,
        "precision": -23,
        "processor": "x86_64",
        "refid": "100.66.246.50",
        "reftime": "e93a0505.8336edfd",
        "rootdelay": 1.026,
        "rootdisp": 8.218,
        "stratum": 2,
        "sys jitter": 0.082849,
        "system": "Linux/5.10.0-26-amd64",
        "test": True,
        "version": "ntpd 4.2.8p15@1.3728-o Wed Sep 23 11:46:38 UTC 2020 (1)",
    }
    assert (
        line_protocol.to_line_protocol(metrics, "ntpmon", additional_tags={"hostname": "ntp1", "processor": "amd64"})
        == "ntpmon,hostname=ntp1,processor=x86_64,refid=100.66.246.50,reftime=e93a0505.8336edfd,system=Linux/5.10.0-26-amd64,"
        "version=ntpd\\ 4.2.8p15@1.3728-o\\ Wed\\ Sep\\ 23\\ 11:46:38\\ UTC\\ 2020\\ (1) "
        "frequency=-11.673,offset=1.45826e-05,rootdelay=1.026,rootdisp=8.218,"
        f"sys_jitter=0.082849,associd=0i,precision=-23i,stratum=2i,leap=0i,test=1i {now_ns}"
    )


def test_transform_identifier() -> None:
    assert line_protocol.transform_identifier("_chrony") == "chrony"
    assert line_protocol.transform_identifier("-chrony-was-here-") == "chrony_was_here"
    assert line_protocol.transform_identifier("hello, world") == "hello_world"
    assert line_protocol.transform_identifier("a = hello(world)") == "a_hello_world"
    assert line_protocol.transform_identifier("def hello(world) -> str:") == "def_hello_world_str"
