# Changelog

Notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.2] - 2023-10-05

### Added

- Proper changelog entries like this one.

### Fixed

- The Ubuntu PPA includes a backported python3-prometheus-client package which
  fixes the lack of IPv6 support in the prometheus client.
- Restored ntpmon-telegraf service used by juju layer to its previous state.

### Removed

- Support for python versions before 3.8 (due to the above prometheus client
  upgrade).

## [2.0.1] - 2023-10-05

### Added

- Debian packaging, including man pages, which is available from the Ubuntu PPA
  https://launchpad.net/~paulgear/+archive/ubuntu/ntpmon/ for Ubuntu 20.04
  (focal) and 22.04 (jammy) LTS versions.  The Debian package defaults to
  prometheus mode, but this can be configured by changing the contents of
  `/etc/default/ntpmon`.
- Makefile install target, for manual installs
- Some other Makefile targets, mostly for supporting development of Debian
  packages
- `--listen-address` option for directing the prometheus exporter to listen on a
  specific address (defaults to 127.0.0.1)

## [2.0.0] - 2023-09-28

### Added

- auto-detection of NTP implementation
- chrony support
- collectd support
- detection of hours and days in "when" field
- gnuplot-based scripts for loopstats and peerstats and intersection algorithm visualisation
- juju charms reactive layer
- ntpd system metrics (from "ntpq -nc readvar")
- prometheus exporter
- standalone parser for chrony statistics files
- systemd service template
- telegraf support
- unit tests expanded and improved (still needs more work)
- updated documentation

### Fixed

- correctly detect when no NTP server is running
- fix incorrect reversal of WARNING & CRITICAL thresholds
- various display quirks and inconsistencies
- code reformatted for flake8 fixes
- report metrics in seconds rather than milliseconds, to prevent confusion when graphing
- report survivors-offset-mean instead of syncpeer-offset-mean; more closely corresponds with old behaviour

### Removed

- trace checks are now disabled by default, and marked as deprecated
