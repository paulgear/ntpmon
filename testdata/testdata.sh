#!/bin/sh

# This file is part of check_ntpmon - see COPYING.txt for license.

set -e
set -u

mkdir -p $PWD/testdata/tmp
TMPFILE=$(mktemp $PWD/testdata/tmp/XXXXXXXX.tmp)
trap 'rm -f $TMPFILE' 0 1 2 3 15

runtest()
{
    FILE="$1"
    shift
    REVERSE="$@"
    echo -n "."
    #echo "Testing $FILE $REVERSE"
    if ./src/check_ntpmon.py --test < $FILE >$TMPFILE 2>&1; then
	if [ -n "$REVERSE" ]; then
	    echo "ERROR: $1 should have failed for $@:"
	    cat $TMPFILE
	    return 1
	fi
    else
	if [ -z "$REVERSE" ]; then
	    echo "ERROR: $1 FAILED:"
	    cat $TMPFILE
	    return 1
	fi
    fi
    return 0
}

echo -n "Running file-based tests"
for i in testdata/OK/*; do
    runtest $i
done
echo "Complete"
