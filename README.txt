NTPmon
by Paul Gear <github@libertysys.com.au>
Copyright (c) 2015-2019 Paul D. Gear <http://libertysys.com.au/>
Juju layer copyright (c) 2017-2018 Canonical Ltd <https://jaas.ai/ntp>

License: GPLv3 - see COPYING.txt for details


PROMETHEUS EXPORTER: EXPERIMENTAL
---------------------------------

EXPOSE THE HTTP SERVER IN THIS BRANCH TO UNTRUSTED NETWORKS AT YOUR OWN RISK.
NO SECURITY TESTING OR VALIDATION HAS BEEN PERFORMED, AND - AS STATED IN THE
GNU GENERAL PUBLIC LICENSE TERMS - THIS SOFTWARE COMES WITH NO WARRANTY.


Introduction
------------

NTPmon is a program which is designed to report on essential health metrics
for NTP.  It provides a Nagios check which can be used with many alerting
systems, including support for Nagios performance data.  NTPmon can also run
as a daemon for sending metrics to collectd, prometheus, or telegraf.


Prerequisites
-------------

NTPmon is written in python, and requires python 3.3 or later.  It uses
modules from the standard python library, and also requires the psutil
library, which is available from pypi or your operating system repositories.
NTPmon also requires 'ntpq' and 'ntptrace' from the NTP distribution.

On Ubuntu (and probably other Debian-based Linux distributions), you can
install all the prerequisites by running:

    sudo apt-get install ntp python3-psutil python3-prometheus-client


Metrics
-------

NTPmon alerts on the following metrics of the local NTP server:

sync:
    Does NTP have a sync peer?  If not, return CRITICAL, otherwise return OK.

peers:
    Are there more than the minimum number of peers active?  The NTP
    algorithms require a minimum of 3 peers for accurate clock management; to
    allow for failure or maintenance of one peer at all times, NTPmon returns
    OK for 4 or more configured peers, CRITICAL for 1 or 0, and WARNING for
    2-3.

reach:
    Are the configured peers reliably reachable on the network?  Return
    CRITICAL for less than 50% total reachability of all configured peers;
    return OK for greater than 75% total reachability of all configured peers.

offset:
    Is the clock offset from its sync peer (or other peers, if the sync peer
    is not available) acceptable?  Return CRITICAL for 50 milliseconds or more
    average difference, WARNING for 10 ms or more average difference, and OK
    for anything less.

traceloop:
    Is there a sync loop between the local server and the stratum 1 servers?
    If so, return CRITICAL.  Most public NTP servers do not support tracing,
    so for anything other than a loop (including a timeout), return OK.
    Trace loop detection is deprecated, and is not supported for prometheus.

In addition, NTPmon retrieves the following metrics directly from the local
NTP server (using 'ntpq -nc readvar'):
    - offset (as 'sysoffset', to distinguish it from 'offset')
    - sys_jitter (as 'sysjitter', for grouping with 'sysoffset')
    - frequency
    - stratum
    - rootdelay
    - rootdisp
See the NTP documentation for the meaning of these metrics:
https://www.eecis.udel.edu/~mills/ntp/html/ntpq.html#system


Startup delay
-------------

By default, until ntpd has been running for 512 seconds (the minimum time for
8 polls at 64-second intervals), check_ntpmon will return OK (zero return code).
This is to prevent false positives on startup or for short-lived VMs.  To
ignore this safety precaution, use --run-time with a low number (e.g. 1 sec).


Usage
-----

(To do)


To do
-----

- Better/more documentation.
- Expand unit tests.
- Create installer.
