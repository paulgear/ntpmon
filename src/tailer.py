#!/usr/bin/env python3
#
# Copyright:    (c) 2016-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import os
import sys
import time


class Tailer:

    """Implements continuous tailing suitable for logs created by chronyd and
    ntpd. May not be suitable as a general file tailing algorithm.  See the test
    suite for more information about the expected behaviour."""

    def __init__(self, filename) -> None:
        self.filename = filename
        self.first_time = True
        self.clear()

    def clear(self) -> None:
        """Set to initial state, except for the 'first_time' flag."""
        self.file = None
        self.pos = -1
        self.st_ino = -1
        self.st_dev = -1

    def open(self) -> None:
        """Open the file.  If this is the first time we've opened it, seek to
        the end."""
        try:
            self.file = open(self.filename, "r")
            whence = os.SEEK_END if self.first_time else os.SEEK_SET
            self.file.seek(0, whence)
            self.pos = self.file.tell()
            stat = os.stat(self.file.fileno())
            self.st_ino = stat.st_ino
            self.st_dev = stat.st_dev
        except OSError:
            self.clear()
        finally:
            self.first_time = False

    def readlines(self) -> list[str]:
        """Read all of the remaining lines in the currently-open file."""
        try:
            self.file.seek(0, os.SEEK_END)
            pos = self.file.tell()
            if pos == self.pos:
                # no change to file; do nothing
                return None
            elif pos < self.pos:
                # file has been truncated; reset to beginning and read all lines
                print(f"Truncated: {pos=} {self.pos=}", file=sys.stderr)
                self.file.seek(0, os.SEEK_SET)
            else:
                # Even if we were in the right place already, we need to set our
                # position to there to keep readlines() happy.
                self.file.seek(self.pos, os.SEEK_SET)

            # we have some data to read
            lines = self.file.readlines()
            self.pos = self.file.tell()
            return lines
        except OSError:
            pass

    def tail(self) -> list[str]:
        """Get the lines from the file.  Handle the case where the file is not
        yet open, or if it has been deleted and recreated."""
        if self.file is None:
            self.open()
            return None

        # Ensure that the file we have open is the filename we previously opened.
        stat = None
        try:
            stat = os.stat(self.filename)
        except OSError:
            pass

        reopen = False
        if stat is None:
            # file deleted - read the rest of it (if any) and reopen when available
            print("Deleted file", file=sys.stderr)
            reopen = True
        elif stat.st_ino != self.st_ino or stat.st_dev != self.st_dev:
            # It's a different file; read the rest of the open one, then open the
            # new one.
            print(f"Different file: {stat.st_ino=} {self.st_ino=} {stat.st_dev=} {self.st_dev=}", file=sys.stderr)
            reopen = True
        else:
            # Same file, just read any lines
            pass

        lines = self.readlines()
        if reopen:
            self.open()
        return lines


def tailf(filename) -> None:
    """Emulate 'tail -F' for a single file."""
    tailer = Tailer(filename)
    while True:
        lines = tailer.tail()
        if lines is not None:
            for l in lines:
                print(l.rstrip("\n"))
        time.sleep(1)


if __name__ == "__main__":
    tailf(sys.argv[1])
