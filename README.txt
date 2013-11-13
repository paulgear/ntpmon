NTPmon
by Paul Gear <ntpmon@libertysys.com.au>
Copyright (c) 2010-2011 Gear Consulting Pty Ltd <http://libertysys.com.au/>

License Statement
-----------------

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.


Introduction
------------

NTPmon is a utility which is designed to monitor and display essential
health metrics for NTP (Network Time Protocol) servers.  Accurate time is
essential to maintaining a functional network, and NTPmon is designed to
help you work out whether your NTP servers are, in fact, doing what they're
supposed to and keeping accurate time.

"Essential" health metrics means a minimal number of metrics which should be
understandable to non-specialists, simply presented.  NTPmon does not aim or
claim to be the last word on NTP monitoring.  Much the opposite - it is more
like the first word, and more advanced tools are both desirable and
necessary if you require highly accurate time.  If you are a time
synchronization geek, NTPmon is not for you - or at least, it's unlikely to
offer you anything more than a quick overview.

Many system administrators don't understand NTP well enough to configure it
correctly for their environment, and some vendors' NTP documentation is
rather lacking, or even just plain wrong.  Before i wrote NTPmon, i searched
for a tool that would monitor NTP for me, but everything i found merely
checked that the daemon was running or that the NTP port was reachable.
These are useful things, but they don't tell you what you really need to
know about your NTP servers.  Hence, i created NTPmon.


Feedback
--------

I am hungry for feedback about NTPmon.  If it works for you, or doesn't work
for you, or pleases you, or doesn't please you, or has great metrics, or has
really bad metrics, please drop me a line at <ntpmon@libertysys.com.au>.


Features
--------

NTPmon connects to your NTP servers to run a peer query using the command
'ntpq -pn <hostname>'.  It parses the output, collects important metrics for
determining NTP server health, and logs them into an RRD for each host.

NTPmon's main web interface shows an overview of all known NTP servers,
along with visual indicators of health for each server.  Clicking on the
server's name provides detailed information for that server, including
graphs of the key metrics.

At the moment, NTPmon is set to poll all known NTP servers every minute
sequentially.  If a large number of hosts is monitored, the time to poll may
exceed one minute, in which case it may be necessary to poll in parallel
rather than serial.  The sample (largely untested) script ntpmon-all shows a
sample of how this might be achieved.

The network bandwidth required to run 'ntpq -pn' for a host is fairly low,
so there should be no need to run a separate NTPmon host for every site,
unless you run a very large number of NTP servers.  My test server has no
difficulty polling another server across an OpenVPN connection where both
ends use consumer-grade ADSL.


Selecting the NTPmon host
-------------------------

One important note about selection of a host to run NTPmon: the accuracy of
the NTPmon host's own clock is important, since all of the data stored by
RRD is time-stamped.  This means generally that the host running NTPmon
should be a standalone host, not a VM or VM server (both Xen and VMware seem
to be less accurate at timekeeping than the vanilla Linux kernel).  It also
should generally be a lightly-loaded host with few or no other critical jobs
to do.  If you have a network large enough to require NTPmon, you can
probably spare a 3- or 4-year-old desktop or server to dedicate to this
task.


Prerequisites
-------------

NTPmon is written in perl.  It requires the following modules from perl's
CPAN library:
	CGI
	File::Basename
	Getopt::Long
	RRDs
	Scalar::Util
	Unix::Syslog

Most of these prerequisites are likely installed on your system already, but
if they are not, please continue reading below.

A web server configured for CGI programs is required.  Apache 2 is the only
tested web server at this stage.  Depending on your distribution, you may
need to enable apache2 to start on boot, and restart it after the
installation of ntpmon.


Versioning
----------

NTPmon uses the same versioning scheme as the Linux kernel: minor releases
(the second component of the version number) are even for stable versions
and odd for development versions.  For example, 0.2.1 is a stable release,
and 0.3.1 is a development release.  I will attempt to make only bug fixes
in the stable releases and reserve new features and gratuitous changes for
development versions.


Installation
------------

To install NTPmon, check that the directory names at the top of Makefile are
appropriate for your distribution, then run
	make install
if you need to change any variables, include them on the command line like
this (example is for SLES 10):
	make install CGI=/srv/www/cgi-bin WWW=wwwrun


Installation examples
---------------------

Assuming that you have the ntpmon files in your current directory, on Debian
and Ubuntu Linux, ntpmon and its prerequisites may be installed by running
the following commands as root:
	apt-get install apache2 librrds-perl libunix-syslog-perl make \
		perl-modules
	make install
	service apache2 restart

(The following may be out of date - I don't test NTPmon on these platforms
regularly.)

On SUSE Linux Enterprise Server (SLES) 10, use the following commands:
	zypper install apache2 perl perl-Unix-Syslog rrdtool
	chkconfig apache2 on
	make install CGI=/srv/www/cgi-bin WWW=wwwrun
	service apache2 restart

On CentOS Linux, use the following commands:
	yum install httpd perl-Unix-Syslog rrdtool-perl
	chkconfig httpd on
	make install WWW=apache CGI=/var/www/cgi-bin APACHE=/etc/httpd/conf.d
	service httpd restart
You must have the EPEL repository enabled for this to work.


Configuration
-------------

By default, NTPmon does not monitor any hosts.  To add a host for
monitoring, simply run '/usr/lib/cgi-bin/ntpmon collect HOSTNAME', and the
host named HOSTNAME will be added to NTPmon's databases.  It will take a few
minutes for the host to be displayed correctly.

No further intervention should be necessary for NTPmon to work, but there
may be configuration required in your firewall or NTP server itself to allow
your NTPmon server permission to query the NTP server.  The basic rule is:
if you can see valid output with 'ntpq -pn HOSTNAME', NTPmon should work for
that host.


Using NTPmon
------------

To see what NTPmon has collected, visit the URL
    http://your.server.example.com/cgi-bin/ntpmon
where your.server.example.com is the hostname of the server where you
installed NTPmon.

