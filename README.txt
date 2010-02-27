Introduction
------------
NTPmon is a web-based utility which is designed to monitor and display
essential health metrics for NTP (Network Time Protocol) servers.  Accurate
time is essential to maintaining a secure and functional network, and NTPmon is
designed to help you work out whether your NTP servers are, in fact, doing what
they're supposed to and keeping your clocks accurate.

Many system administrators 


Features
--------


Selecting the NTPmon host
-------------------------


Prerequisites
-------------

NTPmon is written in perl.  It requires the following modules from perl's CPAN
library:
	CGI
	File::Basename
	Getopt::Long
	RRDs
	Scalar::Util
Most of these prerequisites are likely install on your system already, but if
they are not, please continue reading below.

On Debian (lenny) and Ubuntu (karmic) Linux, all of these prerequisites may be
installed by running the following command as root:
	apt-get install librrds-perl perl-modules

On SUSE Linux Enterprise Server (SLES) 10, these prerequisites may be installed
by running the following command as root:
	zypper install perl rrdtool

Installation
------------

To install NTPmon, run
	make install
from this directory.


Usage
-----

