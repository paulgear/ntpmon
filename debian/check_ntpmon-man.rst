:Version: 2.1.0
:Date: 2023-09-28
:Copyright: 2015-2023 Paul Gear
:Title: check_ntpmon
:Subtitle: NTPmon Nagios check
:Manual group: NTP metrics monitor
:Manual section: "8"

Summary
#######

``check_ntpmon`` is a Nagios-compatible health check which queries data from
the running NTP service and reports overall health and current statistics to
standard output, as well as returning the corresponding exit status.

Usage
#####

usage: check_ntpmon.py [-h]
                       [--check [{proc,offset,peers,reach,reachability,sync,trace,vars} ...]]
                       [--debug] [--run-time RUN_TIME] [--test]

Common Options
##############

options:
  -h, --help            show this help message and exit
  --check [{proc,offset,peers,reach,reachability,sync,trace,vars} ...]
                        Select checks to run; if omitted, run all checks
                        except trace.
  --debug               Include command output and internal state dump along
                        with check results.
  --run-time RUN_TIME   Time in seconds (default: 512) for which to always
                        return OK after NTP daemon startup.
  --test                Obtain peer stats on standard input instead of from
                        running daemon.
