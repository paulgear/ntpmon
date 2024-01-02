#
# Copyright:    (c) 2023-2024 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import version_data

_version = None


def get_version() -> str:
    global _version
    if _version is None:
        _version = ".".join((str(version_data.MAJOR), str(version_data.MINOR), str(version_data.PATCH)))
    return _version
