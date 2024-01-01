#
# Copyright:    (c) 2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import version_data


def get_version() -> str:
    return ".".join((str(version_data.MAJOR), str(version_data.MINOR), str(version_data.PATCH)))
