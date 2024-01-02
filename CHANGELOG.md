# Changelog

Notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project (mostly) adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

Semantic Versioning dictates that only the 0.y.z version should undergo rapid
changes.  This project differs in that I want to be able to undertake rapid
changes at multiple stages after stable versions have been released.  Hence,
from version 3.x onwards NTPmon will use a versioning style somewhat like the
Linux kernel original versioning scheme, where odd-numbered major versions are
development releases, which can have backwards incompatible changes introduced
over the lifetime of that major version. Even-numbered major versions will be
stable releases which will only contain new features and bug fixes.

The current stable release is 2.1.0.  It will be receiving no further
development unless critical security or data integrity bugs are found.

The current development release is 3.0.6.  This is the recommended version for
anyone who wants the latest features.  It should be suitable for production
deployment very soon.

## [3.0.5] - 2023-12-30

### Changed

- Fix incorrect function decorator preventing startup in telegraf mode.
- Ensure the ntpmon user is in the chrony or ntp system groups if they are
  present.  This fixes the inability to read chrony logs by default on Debian
  and Ubuntu.
- Add test suite for line_protocol and fix some resultant bugs.
- Reduce polling frequency on peer stats log to once every 3 seconds.

## [3.0.4] - 2023-12-29

### Changed

- Ensure test suite is timezone-independent.

## [3.0.3] - 2023-12-29

### Changed

- Complete fixing of typing to restore compatibility with python 3.8.

## [3.0.2] - 2023-12-28

### Changed

- Fixed typing to restore compatibility with python 3.8.
- Fixed broken Debian build dependencies.

## [3.0.1] - 2023-12-27

### Changed

- Update Makefile to help me remember the correct packaging workflow.

## [3.0.0] - 2023-12-27

### Changed

- Added individual peer stats (derived from chronyd's measurements.log or ntpd's
  peerstats) to metrics output.  These are automatically detected in the default
  locations of /var/log/chrony/measurements.log and /var/log/ntpstats/peerstats
  and emitted automatically to telegraf or the prometheus exporter.
- Added --logfile command line option to allow changing the above defaults.
- Reformatted all code with 'black' (see Makefile 'format' target).  Please use
  this Makefile target before submitting any pull requests.
- Updated license to AGPLv3.
- Removed trace-related metrics.
- Removed juju layer.
- Clean up internal structure:
  - outputs.py now provides a class structure for encapsulating knowledge about
    collectd, prometheus, and telegraf
  - alert.py and ntpmon.py no longer have special casing for the mode
  - all argument processing and defaults selection is done in get_args()
- Some collectd data types have been updated to reflect the defaults available
  in version 5.12.  I'm considering deprecating collectd support in a near
  future version.  If you are using ntpmon with collectd and would prefer this
  support not to go away, please let me know.

## [2.1.0] - 2023-12-22

### Changed

- Readme updated to reflect PPA installation.
- Changed Debian dependency on python3-prometheus-client to a recommendation,
  because it is only required when using the prometheus exporter.

### Removed

- Metrics with no values are no longer displayed via the Nagios check, because
  [they break icinga2's
  GraphiteWriter](https://github.com/paulgear/ntpmon/pull/26).  Whilst this is
  technically a breaking change, it only affects the deprecated trace-related
  metrics, which are disabled by default, so I'm declaring this a minor release.
  Removal of the trace-related metrics will be completed in a future release.
- Removed warning about lack of IPv6 support in python3-prometheus-client, since
  a fixed version is shipped in the PPA.

## [2.0.2] - 2023-10-05

### Added

- Proper changelog entries like this one.

### Changed

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
