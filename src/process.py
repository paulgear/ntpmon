#!/usr/bin/env python3
#
# Copyright:    (c) 2016-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import subprocess
import sys
import time

import psutil

from peers import NTPPeers
from readvar import NTPVars


_logfiles = {
    "chronyd": "/var/log/chrony/measurements.log",
    "ntpd": "/var/log/ntpstats/peerstats",
}

_progs = {
    "chronyd": {
        "peers": "chronyc -c sources",
        "vars": "chronyc -c tracking",
    },
    "ntpd": {
        "peers": "ntpq -pn",
        "vars": "ntpq -nc readvar",
    },
}


def execute_subprocess(cmd, timeout, debug, errfatal):
    try:
        output = subprocess.check_output(
            cmd,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=timeout,
            universal_newlines=True,
        )
    except subprocess.CalledProcessError as cpe:
        # FIXME: should be a metric rather than fatal error
        if errfatal:
            fatal(
                "%s returned %d: %s"
                % (
                    " ".join(cpe.cmd),
                    cpe.returncode,
                    cpe.stderr,
                )
            )
    except subprocess.TimeoutExpired as te:
        if debug:
            print(te)
        output = te.output
    return output


def detect_implementation():
    """Attempt to detect implementation based on the name of the running NTP server process."""
    implementation = NTPProcess()
    if implementation.getprocess() is None:
        return None
    if implementation.name:
        return implementation.name
    else:
        return None


# cache implementation for the lifetime of ntpmon
cached_implementation: str = None


def get_implementation() -> str:
    """Return the implementation, if one is detected, or None."""
    global cached_implementation
    if cached_implementation is None:
        cached_implementation = detect_implementation()
    return cached_implementation


def get_logfile(implementation) -> str:
    """Return the location of the peer measurements log for this implementation, or None, if one cannot be detected."""
    return _logfiles.get(implementation, None)


def get_progs(implementation):
    """Return the dict of programs for this implementation, or None, if one cannot be detected."""
    if implementation in _progs:
        return _progs[implementation]

    implementation = detect_implementation()
    if implementation in _progs:
        return _progs[implementation]
    else:
        return None


def execute(prog, timeout=30, debug=False, errfatal=False, implementation=None):
    """
    Execute a predefined external command.  Return the output and the elapsed time in seconds.
    """
    progs = get_progs(implementation)
    if progs is None:
        return None
    if prog not in progs:
        return None

    failmessage = "%s produced no output.  Please check that an NTP server is installed and running."

    output = None
    cmd = progs[prog].split()
    start = time.time()
    output = execute_subprocess(cmd, timeout=timeout, debug=debug, errfatal=errfatal)
    elapsed = time.time() - start

    if output is None or len(output) == 0:
        if errfatal:
            # FIXME: should be a metric rather than fatal error
            fatal(failmessage % progs[prog])
        else:
            return [[], elapsed]
    else:
        if debug:
            print(output)
            print("elapsed time: %.3f seconds" % (elapsed,))
        return [output.split("\n"), elapsed]


def fatal(msg):
    print("UNKNOWN: " + msg, file=sys.stderr)
    sys.exit(3)


def ntpchecks(checks, debug, implementation=None):
    """
    Run all of the checks required by the argument list
    and return the resulting objects in a hash.
    """
    objs = {}

    if implementation not in _progs:
        implementation = detect_implementation()

    if "proc" in checks:
        objs["proc"] = NTPProcess()

    if implementation is None:
        return objs

    for check in checks:
        if (check in ["offset", "peers", "reach", "sync"]) and "peers" not in objs:
            (output, elapsed) = execute("peers", debug=debug, implementation=implementation)
            objs["peers"] = NTPPeers(output, elapsed)
            break

    if "vars" in checks:
        (output, elapsed) = execute("vars", debug=debug, implementation=implementation)
        objs["vars"] = NTPVars(output, elapsed)

    return objs


class NTPProcess(object):
    def __init__(self, names=None):
        """
        Save which process names we're looking for, and the version of psutil.
        """
        if names is None:
            self.names = ["chronyd", "ntpd"]
        else:
            self.names = names
        # Check for old psutil per http://grodola.blogspot.com.au/2014/01/psutil-20-porting.html
        self.PSUTIL2 = psutil.version_info >= (2, 0)

    def getprocess(self):
        """
        Search the process table for a matching process name.
        Return the psutil process object.
        """
        for proc in psutil.process_iter():
            try:
                name = proc.name() if self.PSUTIL2 else proc.name
                if name in self.names:
                    self.name = name
                    return proc
            except psutil.Error:
                pass
        return None

    def getruntime(self):
        """
        Return the length of time in seconds that the process has been running.
        If process is not running or any error occurs, return -1.
        """
        proc = self.getprocess()
        if proc is None:
            return -1
        try:
            now = time.time()
            create_time = proc.create_time() if self.PSUTIL2 else proc.create_time
            start = int(create_time)
            return now - start
        except psutil.Error:
            return -1

    def getmetrics(self):
        return {"runtime": self.getruntime()}


def main():
    import pprint

    implementation = detect_implementation()
    print("Running {}".format(implementation))
    pprint.pprint(NTPProcess().getmetrics())
    checks = ["offset", "peers", "proc", "reach", "sync", "vars"]
    checkobjs = ntpchecks(checks, debug=True, implementation=implementation)
    from alert import NTPAlerter

    alerter = NTPAlerter(checks)
    alerter.alert(checkobjs, hostname=None, interval=0, format="telegraf")


if __name__ == "__main__":
    main()
