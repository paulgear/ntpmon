#!/usr/bin/env python3
#
# Copyright:    (c) 2024 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import platform
import re
import time

from typing import Dict

import psutil

import process
import version as ntpmon_version

_static_info = None


def get_info(implementation: str, version: str) -> Dict[str, str]:
    """Collect the platform and process info metrics."""
    global _static_info
    if _static_info is None:
        _static_info = {
            "ntpmon_version": ntpmon_version.get_version(),
            "platform_machine": platform.machine(),
            "platform_release": platform.release(),
            "platform_system": platform.system(),
            "python_version": platform.python_version(),
        }

    this_process = psutil.Process()
    memory = this_process.memory_info()
    uptime = time.time() - this_process.create_time()

    dynamic_info = {
        "implementation_name": implementation,
        "implementation_version": extract_version(version),
        "ntpmon_rss": memory.rss,
        "ntpmon_uptime": uptime,
        "ntpmon_vms": memory.vms,
    }

    dynamic_info.update(_static_info)
    return dynamic_info


_version_re = re.compile(r"\b\d\S+")


def extract_version(rawversion: str) -> str:
    """Extract the version string from the line.  Raise ValueError if no match."""
    return _version_re.search(rawversion).group()


if __name__ == "__main__":
    i = process.get_implementation()
    v = process.execute("version")[0][0]
    print(get_info(implementation=i, version=v))
