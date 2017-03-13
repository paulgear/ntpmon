#!/bin/bash
#
# ipset statistics collectd exec plugin
#
# Author: Paul D. Gear
# License: GPLv3
#
# Because collectd requires that plugins run as non-root, this script
# requires ipset output to be in /var/lib/collectd/ipset-NAME.txt
#
# Create /etc/cron.d/collectd-ipset with the following contents:
#    */5 * * * * root /sbin/ipset list NAME > /var/lib/collectd/ipset-NAME.txt
# Where NAME is the name of the ipset you wish to monitor.
#
# Bugs:
#    Order of fields in ipset output is hard-coded
#

SET=$1
NAME=$(echo $SET|tr '-' '_')

HOSTNAME="${COLLECTD_HOSTNAME:-localhost}"
INTERVAL=300

while :; do
	if [ -t 0 ]; then
		date
	fi
	awk '
	START {
		COUNT=0;
		NEWEST=0;
	}
	/^Header: /		{OLDEST=$9}
	/^Size in memory: /	{print "count-memory " $4; next}
	/packets/ {
		COUNT++
		PACKETS+=$5
		BYTES+=$7
		if ($3 < OLDEST) {
			OLDEST=$3
		}
		if ($3 > NEWEST) {
			NEWEST=$3
		}
		next
	}
	END {
		print "count-bytes " BYTES
		print "count-hosts " COUNT
		print "count-packets " PACKETS
		print "timeleft-newest " NEWEST
		print "timeleft-oldest " OLDEST
	}
	' /var/lib/collectd/ipset-$SET.txt | while read key val; do
		echo "PUTVAL $HOSTNAME/ipset-$NAME/$key interval=$INTERVAL N:$val"
	done
	second=$(date +%s)
	(( sleep=INTERVAL - (second % INTERVAL) + 2))
	if [ -t 0 ]; then
		echo sleep $sleep
	fi
	sleep $sleep
done
