#!/usr/bin/env python3
#
# Copyright:    (c) 2016-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

"""
Parse 'chronyc -c tracking' or 'ntpq -nc readvar' output and extract metrics.
"""


# This is lame; these are in exactly the opposite order as in alert.py
_aliases = {
    "offset": "sysoffset",
    "sys_jitter": "sysjitter",
}


def parse_chronyd_vars(vars):
    """Turn a list of values from chronyc into metrics."""
    metrics = {}
    metrics["stratum"] = int(vars[2])
    metrics["systime"] = float(vars[3])
    metrics["sysoffset"] = float(vars[4])
    metrics["lastoffset"] = float(vars[5])
    metrics["rmsoffset"] = float(vars[6])
    metrics["frequency"] = float(vars[7])
    metrics["residualfreq"] = float(vars[8])
    metrics["skew"] = float(vars[9])
    metrics["rootdelay"] = float(vars[10])
    metrics["rootdisp"] = float(vars[11])
    return metrics


def parse_ntpd_vars(vars):
    """Turn a list of name/value pairs separated by equals signs from ntpq into metrics."""
    metrics = {}
    for v in vars:
        nameval = v.split("=")
        if len(nameval) == 2:
            try:
                if nameval[0] in ["rootdelay", "rootdisp"]:
                    # convert from milliseconds to seconds
                    metrics[nameval[0]] = round(float(nameval[1]) / 1000.0, 9)
                elif nameval[0] in _aliases:
                    # convert from milliseconds to seconds, alias
                    metrics[_aliases[nameval[0]]] = round(float(nameval[1]) / 1000.0, 9)
                else:
                    metrics[nameval[0]] = float(nameval[1])
            except ValueError:
                # ignore non-numeric values
                pass
    return metrics


class NTPVars(object):
    def __init__(self, lines=None, elapsed=0):
        if not isinstance(lines, str):
            # multiple lines - join them
            lines = " ".join(lines)

        # single string - split it by commas, remove whitespace
        rv = [v.strip() for v in lines.split(",")]

        # split each string into metric name + value
        if lines.count("=") < 5 and len(rv) >= 12:
            # chronyd has 12 fields, and no equals signs
            self.metrics = parse_chronyd_vars(rv)
        else:
            # otherwise assume ntpd
            self.metrics = parse_ntpd_vars(rv)
        self.metrics["varstime"] = elapsed

    def getmetrics(self):
        return self.metrics


if __name__ == "__main__":
    import pprint
    import process

    lines, elapsed = process.execute("vars", debug=False)
    nv = NTPVars(lines, elapsed)
    v = nv.getmetrics()
    pprint.pprint(v)
