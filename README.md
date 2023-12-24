# NTPmon

Copyright (c) 2015-2023 Paul D. Gear <https://libertysys.com.au/>

Juju layer copyright (c) 2017-2018 Canonical Ltd <https://charmhub.io/ntp>

## License

GPLv3 - see COPYING.txt for details

## Introduction

NTPmon is a program which is designed to report on essential health metrics for
NTP.  It provides a Nagios check which can be used with many alerting systems,
including support for Nagios performance data.  NTPmon can also run as a daemon
for sending metrics to collectd, prometheus, or telegraf.  It supports both
`ntpd` and `chronyd`.

## Installation

On Ubuntu (and possibly other Debian derivatives) NTPmon and its prerequisites
can be installed from [its
PPA](https://launchpad.net/~paulgear/+archive/ubuntu/ntpmon/) using:

    sudo add-apt-repository ppa:paulgear/ntpmon
    sudo apt install chrony ntpmon

`chrony` is the preferred NTP server on Ubuntu; you can also use `ntp` or
`ntpsec` from the universe pool, although the are not guaranteed to receive
security updates unless you use Ubuntu Pro.

If you wish to use something other than the prometheus exporter by default, you
must edit `/etc/default/ntpmon` to configure the command-line options.  Run
`/opt/ntpmon/bin/ntpmon --help` for details of all available options.

## Prerequisites

NTPmon is written in python, and requires python 3.8 or later.  It uses modules
from the standard python library, and also requires the `psutil` library, which
is available from pypi or your operating system repositories. It requires `ntpq`
or `chronyc` to retrieve metrics from the running NTP daemon. If you intend to
run the prometheus exporter, the [prometheus python
client](https://pypi.org/project/prometheus-client/) is also required.

On Ubuntu (and probably other Debian-based Linux distributions), you can install
all the prerequisites by running:

    sudo apt-get install chrony python3-prometheus-client python3-psutil
    # or substitute ntp for the traditional NTP server

## Usage

To run NTPmon directly from source after manually installing the prerequisites:

    cd /opt
    git clone https://github.com/paulgear/ntpmon
    cd ntpmon
    ./src/ntpmon.py --help

## Metrics

NTPmon alerts on the following metrics of the local NTP server:

#### sync

Does NTP have a sync peer?  If not, return CRITICAL, otherwise return OK.

#### peers

Are there more than the minimum number of peers active?  The NTP algorithms
require a minimum of 3 peers for accurate clock management; to allow for failure
or maintenance of one peer at all times, NTPmon returns OK for 4 or more
configured peers, CRITICAL for 1 or 0, and WARNING for 2-3.

#### reach

Are the configured peers reliably reachable on the network?  Return CRITICAL for
less than 50% total reachability of all configured peers; return OK for greater
than 75% total reachability of all configured peers.

#### offset

Is the clock offset from its sync peer (or other peers, if the sync peer is not
available) acceptable?  Return CRITICAL for 50 milliseconds or more average
difference, WARNING for 10 ms or more average difference, and OK for anything
less.

### System metrics

In addition, NTPmon retrieves the following metrics directly from the local NTP
server (using `ntpq -nc readvar`):

- offset (as `sysoffset`, to distinguish it from `offset`)
- sys_jitter (as `sysjitter`, for grouping with `sysoffset`)
- frequency
- stratum
- rootdelay
- rootdisp

See the [NTP documentation](http://doc.ntp.org/current-stable/ntpq.html#system)
for the meaning of these metrics.

### Prometheus exporter

When run in prometheus mode, NTPmon uses the [prometheus python
client](https://pypi.python.org/pypi/prometheus_client) to expose metrics via
the HTTP server built into that library.  No security testing or validation has
been performed on this library by the NTPmon author; users are suggested not to
expose it on untrusted networks, and are reminded that - as stated in the
license terms - this software comes with no warranty.

### Telegraf integration

When run in telegraf mode, NTPmon requires the telegraf [socket
listener](https://docs.influxdata.com/telegraf/v1/plugins/#input-socket_listener)
input plugin to be enabled.  Use the `--connect` command-line option if you
configure this to listen on a host and/or port other than the default
(127.0.0.1:8094).

## Startup delay

By default, until the NTP server has been running for 512 seconds (the minimum
time for 8 polls at 64-second intervals), `check_ntpmon`` will return OK (zero
return code). This is to prevent false positives on startup or for short-lived
VMs.  To ignore this safety precaution, use `--run-time`` with a low number
(e.g. 1 sec).

## To do

- Better/more documentation.
- Better/more unit tests.
