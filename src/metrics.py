#
# Copyright:    (c) 2016-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import math


def _add_alias(metrics, name, alias):
    """
    Add an alias for a single named metric
    """
    if name in metrics and not math.isnan(metrics[name]):
        metrics[alias] = metrics[name]
        return True
    else:
        return False


def _find_alias(metrics, alias, names):
    """
    If a single name is given, find the named metric and add its alias to the hash.
    If names is a list, find the first matching one and add its alias to the hash.
    """
    if names is None:
        names = alias
    if isinstance(names, str):
        # it's a single string; add it
        _add_alias(metrics, names, alias)
    else:
        # it's a list; try each one in order
        for n in names:
            if _add_alias(metrics, n, alias):
                return


def addaliases(metrics, aliases):
    """
    Add all defined aliases to metrics
    """
    for a in aliases:
        _find_alias(metrics, a, aliases[a])
