#!/usr/bin/env python3
#
# Copyright:    (c) 2024 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import info

version_tests = {
    "4.2": "chronyd (chrony) version 4.2 (+CMDMON +NTP +REFCLOCK +RTC +PRIVDROP +SCFILTER +SIGND +ASYNCDNS +NTS +SECHASH +IPV6 -DEBUG)",
    "4.2.8p15@1.3728-o": "ntpd 4.2.8p15@1.3728-o Wed Sep 23 11:46:38 UTC 2020 (1)",
    "5.10.0-26-amd64": "Linux ntp5 5.10.0-26-amd64 #1 SMP Debian 5.10.197-1 (2023-09-29) x86_64 GNU/Linux",
    "1.12.28-0+deb11u1": "ii  dbus           1.12.28-0+deb11u1  amd64  simple interprocess messaging system (daemon and utilities)",
    "2.4.52-1ubuntu4.7": "ii  apache2-utils  2.4.52-1ubuntu4.7  amd64  Apache HTTP Server (utility programs for web servers)",
}


def test_get_info() -> None:
    i = info.get_info(implementation="myntp", version="myntp1 1.2.3-beta1 test")
    for field in ["platform_machine", "platform_release", "platform_system", "ntpmon_version"]:
        assert field in i
        assert type(i[field]) == str

    assert i["implementation_name"] == "myntp"
    assert i["implementation_version"] == "1.2.3-beta1"
    assert i["resident_set_size"] > 1000
    assert i["uptime"] > 0.000001
    assert i["virtual_memory_size"] > i["resident_set_size"]
    assert [int(x) for x in i["python_version"].split(".")] >= [3, 8, 0]


def test_extract_version() -> None:
    for k, v in version_tests.items():
        assert info.extract_version(v) == k
