NTPmon version 0.1.3
by Paul Gear <ntpmon@libertysys.com.au>
Copyright (c) 2010 Liberty Systems & Software <http://libertysys.com.au/>
Free Software, released under GNU GPLv3.

Introduction
------------

NTPmon is a utility which is designed to monitor and display essential health
metrics for NTP (Network Time Protocol) servers.  Accurate time is essential to
maintaining a functional network, and NTPmon is designed to help you work out
whether your NTP servers are, in fact, doing what they're supposed to and
keeping accurate time.

Many system administrators don't understand NTP well enough to configure it
correctly for their environment, and some vendors' NTP documentation is rather
lacking, or even just plain wrong.  Before i wrote NTPmon, i searched for a
tool that would monitor NTP for me, but everything i found merely checked that
the daemon was running or that the NTP port was reachable.  These are useful
things, but they don't tell you what you really need to know about your NTP
servers.  Hence, i created NTPmon.


Features
--------

NTPmon connects to your NTP servers to run a peer query using the command 'ntpq
-pn <hostname>'.  It parses the output, collects important metrics for
determining NTP server health, and logs them into an RRD for each host.

NTPmon's main web interface shows an overview of all known NTP servers, along
with visual indicators of health for each server.  Clicking on the server's
name provides detailed information for that server, including graphs of the key
metrics.

At the moment, NTPmon is set to poll all known NTP servers every minute
sequentially.  If a large number of hosts is monitored, the time to poll may
exceed one minute, in which case it may be necessary to poll in parallel rather
than serial.  The sample (largely untested) script ntpmon-all shows a sample of
how this might be achieved.


Selecting the NTPmon host
-------------------------

One important note about selection of a host to run NTPmon: the accuracy of the
NTPmon host's own clock is crucial, since all of the data stored by RRD is
time-stamped.  This means generally that the host running NTPmon should be a
standalone host, not a VM or VM server (both Xen and VMware seem to be less
accurate at timekeeping than the vanilla Linux kernel).  It also should
generally be a lightly-loaded host with few or no other critical jobs to do.
If you have a network large enough to require NTPmon, you can probably spare a
3- or 4-year-old desktop or server to dedicate to this task.


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

Depending on your distribution, you may also need to enable apache2 to start on
boot by running
	chkconfig apache2 on
or similar, and starting it with
	service apache2 start
or similar.


Installation
------------

To install NTPmon, check that the directory names at the top of Makefile are
appropriate for your distribution, then run
	make install
if you need to change any variables, include them on the command line like this (example is for SLES 10):
	make install CGI=/srv/www/cgi-bin WWW=wwwrun


Configuration
-------------

By default, NTPmon does not monitor any hosts.  To add a host for monitoring,
simply run '/usr/lib/cgi-bin/ntpmon collect HOSTNAME', and the host named
HOSTNAME will be added to NTPmon's databases.  It will take a few minutes for
the host to be displayed correctly.

No further intervention should be necessary for NTPmon to work, but there may
be configuration required in your firewall or NTP server itself to allow your
NTPmon server permission to query the NTP server.  The basic rule is: if you
can see valid output with 'ntpq -pn HOSTNAME', NTPmon should work for that
host.


Feedback
--------

As always, i am hungry for feedback about NTPmon.  If it works for you, or
doesn't work for you, or pleases you, or doesn't please you, or has great
metrics, or has really bad metrics, please drop me a line at
<ntpmon@libertysys.com.au>.

