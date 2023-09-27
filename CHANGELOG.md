# Changelog

Notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


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
