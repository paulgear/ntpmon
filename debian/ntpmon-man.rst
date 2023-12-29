:Version: 3.0.2
:Date: 2023-12-28
:Copyright: 2015-2023 Paul Gear
:Title: ntpmon
:Subtitle: NTP metrics monitor
:Manual group: NTP metrics monitor
:Manual section: "8"

Summary
#######

``ntpmon`` is a metrics collector for NTP which periodically queries data from
the running NTP service and sends it to ``collectd``, ``prometheus``, or
``telegraf`` for graphing or further processing.

Usage
#####

ntpmon.py [-h] [--mode {collectd,prometheus,telegraf}] [--connect CONNECT]
          [--interval INTERVAL] [--listen ADDRESS] [--port PORT]

Common Options
##############

Options:

  -h, --help            show this help message and exit

  --mode {collectd,prometheus,telegraf}
                        Collectd is the default if collectd environment
                        variables are detected

  --connect CONNECT     Connect string (in host:port format) to use when sending
                        data to telegraf (default: 127.0.0.1:8094)

  --interval INTERVAL   How often to report statistics (default: the value of
                        the COLLECTD_INTERVAL environment variable, or 60
                        seconds if COLLECTD_INTERVAL is not set)

  --listen-address LISTEN_ADDRESS
                        IPv4/IPv6 address on which to listen when acting as a
                        prometheus exporter (default: 127.0.0.1)

  --port PORT           TCP port on which to listen when acting as a prometheus
                        exporter (default: 9648)
