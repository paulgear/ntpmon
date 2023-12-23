#!/usr/bin/env python3

import logging
import os
import sys
import time


log = logging.getLogger(__name__)

class Tailer:

    def __init__(self, filename) -> None:
        self.filename = filename
        self.file = None
        self.pos = -1
        self.st_ino = -1
        self.st_dev = -1

    def open(self) -> None:
        """Open the file and seek to the end"""
        try:
            self.file = open(self.filename, 'r')
            self.file.seek(0, os.SEEK_END)
            self.pos = self.file.tell()
            stat = os.stat(self.file.fileno())
            self.st_ino = stat.st_ino
            self.st_dev = stat.st_dev
        except OSError:
            pass

    def readlines(self) -> list[str]:
        """Read all of the remaining lines in the currently-open file"""
        try:
            self.file.seek(0, os.SEEK_END)
            pos = self.file.tell()
            if pos == self.pos:
                # no change to file; do nothing
                return None
            elif pos < self.pos:
                # file has been truncated; reset to beginning and read all lines
                log.warning("Truncated")
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
        stat = os.stat(self.filename)
        if stat.st_ino != self.st_ino or stat.st_dev != self.st_dev:
            # It's a different file; read the rest of this one, then open the
            # new one.  (This call to readlines() could be combined with the
            # following one, but the logic is clearer if they are separate.)
            lines = self.readlines()
            self.open()
            return lines
        else:
            return self.readlines()


def tailf(filename) -> None:
    """Emulate 'tail -F' for a single file."""
    tailer = Tailer(filename)
    while True:
        lines = tailer.tail()
        if lines is not None:
            for l in lines:
                print(l.strip())
        time.sleep(1)


if __name__ == "__main__":
    tailf(sys.argv[1])
