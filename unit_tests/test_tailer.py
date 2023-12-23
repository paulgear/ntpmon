import os
import sys
from tempfile import NamedTemporaryFile

from tailer import Tailer


def test_tail_new_file() -> None:
    f = NamedTemporaryFile(mode="wt")
    tailer = Tailer(f.name)
    lines = tailer.tail()
    assert lines is None

    datalines = ["Hello, world"]
    f.writelines(datalines)
    f.flush()
    lines = tailer.tail()
    assert lines == datalines

    # if we keep reading we shouldn't get any more data
    assert tailer.tail() is None


def test_tail_existing_file() -> None:
    f = NamedTemporaryFile(mode="wt")
    datalines = [
        "Hello, world\n",
        "How's it going?\n",
        "Be excellent to each other.\n",
        "Party on, dudes!\n",
    ]
    f.writelines(datalines)
    f.close()

    tailer = Tailer(f.name)
    for i in range(3):
        lines = tailer.tail()
        assert lines is None


def test_tail_log_file() -> None:
    initial_datalines = [
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 query[A] connectivity-check.ubuntu.com from 2001:db8:100::2\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 forwarded connectivity-check.ubuntu.com to 2001:db8:100:1::3\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.48\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 35.232.111.17\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.49\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 91.189.91.49\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 34.122.121.32\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.18\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 91.189.91.48\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 35.224.170.84\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.17\n",
    ]
    add_datalines = [
        [
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 query[A] captive.g.aaplimg.com from 2001:db8:100::2\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 forwarded captive.g.aaplimg.com to 2001:db8:100:1::3\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 query[AAAA] captive.g.aaplimg.com from 2001:db8:100::2\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 forwarded captive.g.aaplimg.com to 2001:db8:100:1::3\n",
        ],
        [
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 reply captive.g.aaplimg.com is 2403:300:a08:f100::2\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 reply captive.g.aaplimg.com is 2403:300:a08:f100::6\n",
        ],
        [
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 reply captive.g.aaplimg.com is 17.253.67.205\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 reply captive.g.aaplimg.com is 17.253.67.201\n",
        ],
    ]
    f = NamedTemporaryFile(mode="wt")
    f.writelines(initial_datalines)
    f.flush()

    tailer = Tailer(f.name)
    # initially we seek to the end and shouldn't get any data
    assert tailer.tail() is None

    # write and tail the file
    for i in range(len(add_datalines)):
        f.writelines(add_datalines[i])
        f.flush()
        lines = tailer.tail()
        assert lines == add_datalines[i]

    # if we keep reading we shouldn't get any more data
    assert tailer.tail() is None


def test_tail_truncate() -> None:
    """This tests the case where the log is truncated and new data written,
    the total length of which is less than the existing end position. This
    should be the normal case for log files which use logrotate's copytruncate
    or an equivalent method."""
    initial_datalines = [
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 query[A] connectivity-check.ubuntu.com from 2001:db8:100::2\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 forwarded connectivity-check.ubuntu.com to 2001:db8:100:1::3\n",
    ]
    pre_truncate_datalines = [
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.48\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 35.232.111.17\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.49\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 91.189.91.49\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 34.122.121.32\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.18\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 91.189.91.48\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 35.224.170.84\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.17\n",
    ]
    post_truncate_datalines = [
        [
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 query[A] captive.g.aaplimg.com from 2001:db8:100::2\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 forwarded captive.g.aaplimg.com to 2001:db8:100:1::3\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 query[AAAA] captive.g.aaplimg.com from 2001:db8:100::2\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 forwarded captive.g.aaplimg.com to 2001:db8:100:1::3\n",
        ],
        [
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 reply captive.g.aaplimg.com is 2403:300:a08:f100::2\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 reply captive.g.aaplimg.com is 2403:300:a08:f100::6\n",
        ],
        [
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 reply captive.g.aaplimg.com is 17.253.67.205\n",
            "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 reply captive.g.aaplimg.com is 17.253.67.201\n",
        ],
    ]
    f = NamedTemporaryFile(mode="wt")
    f.writelines(initial_datalines)
    f.flush()

    tailer = Tailer(f.name)
    # initially we seek to the end and shouldn't get any data
    assert tailer.tail() is None

    # write more lines
    f.writelines(pre_truncate_datalines)
    f.flush()

    # if the tailer wakes up now it should get those lines
    lines = tailer.tail()
    assert lines == pre_truncate_datalines

    # truncate the file
    f.truncate()
    f.flush()

    # write and tail the file normally
    for i in range(len(post_truncate_datalines)):
        f.writelines(post_truncate_datalines[i])
        f.flush()
        lines = tailer.tail()
        assert lines == post_truncate_datalines[i]

    # if we keep reading we shouldn't get any more data
    assert tailer.tail() is None


def test_tail_truncate_bad_timing() -> None:
    """This tests the case where new data is written, the log is truncated,
    and then more new data is written, (the total length of which is less than
    the existing end position), but the tailer is not invoked in time to see the
    first data written to the file. In this case the data written pre-truncate
    is lost.  This is unavoidable when using a poll-based tailer, and that's why
    closing, moving, and recreating the file is the normal method for most log
    rotation strategies."""
    initial_datalines = [
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 query[A] connectivity-check.ubuntu.com from 2001:db8:100::2\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 forwarded connectivity-check.ubuntu.com to 2001:db8:100:1::3\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.48\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 35.232.111.17\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.49\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 91.189.91.49\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 34.122.121.32\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.18\n",
        "Dec 23 13:28:49 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 91.189.91.48\n",
    ]
    pre_truncate_datalines = [
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 35.224.170.84\n",
        "Dec 23 13:28:50 firewall dnsmasq[618230]: 5338042 2001:db8:100::2/49897 reply connectivity-check.ubuntu.com is 185.125.190.17\n",
    ]
    post_truncate_datalines = [
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 query[A] captive.g.aaplimg.com from 2001:db8:100::2\n",
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 forwarded captive.g.aaplimg.com to 2001:db8:100:1::3\n",
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 query[AAAA] captive.g.aaplimg.com from 2001:db8:100::2\n",
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 forwarded captive.g.aaplimg.com to 2001:db8:100:1::3\n",
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 reply captive.g.aaplimg.com is 2403:300:a08:f100::2\n",
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337763 2001:db8:100::2/56159 reply captive.g.aaplimg.com is 2403:300:a08:f100::6\n",
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 reply captive.g.aaplimg.com is 17.253.67.205\n",
        "Dec 23 13:29:11 firewall dnsmasq[618230]: 5337762 2001:db8:100::2/44016 reply captive.g.aaplimg.com is 17.253.67.201\n",
    ]
    f = NamedTemporaryFile(mode="wt", delete=False)
    f.writelines(initial_datalines)
    f.flush()

    tailer = Tailer(f.name)
    # initially we seek to the end and shouldn't get any data
    assert tailer.tail() is None

    # write more lines
    f.writelines(pre_truncate_datalines)
    f.close()

    # the tailer doesn't get woken up in time...

    # truncate the file
    f = open(f.name, "w+")

    # write and tail the file - the pre_truncate_datalines are lost because the
    # tailer didn't get woken up to read them quickly enough
    f.writelines(post_truncate_datalines)
    f.flush()
    lines = tailer.tail()
    assert lines == post_truncate_datalines

    # if we keep reading we shouldn't get any more data
    assert tailer.tail() is None
    os.unlink(f.name)


def test_tail_truncate_longer_data() -> None:
    """This tests the case where the log is truncated and new data written,
    the total length of which is greater than the existing end position. In this
    scenario, a polling tailer is unable to detect the truncation and will
    simply continue from the existing position marker."""
    initial_datalines = [
        "hello\n",
        "world\n",
    ]
    truncate_datalines = [
        "supercalifragilisticexpialidocious\n",
    ]
    f = NamedTemporaryFile(mode="wt", delete=False)
    f.writelines(initial_datalines)
    f.flush()

    tailer = Tailer(f.name)
    # initially we seek to the end and shouldn't get any data
    assert tailer.tail() is None

    # the tailer doesn't get woken up in time...

    # truncate the file & write more lines
    f = open(f.name, "w+")
    f.writelines(truncate_datalines)
    f.close()

    # tail the file - we should only get the parts past the previous marker
    saved_pos = tailer.pos
    lines = tailer.tail()
    assert lines == [truncate_datalines[0][saved_pos:]]

    # if we keep reading we shouldn't get any more data
    assert tailer.tail() is None
    os.unlink(f.name)


def test_no_file_present() -> None:
    """This tests the case where the file doesn't exist when we start tailing."""
    initial_datalines = [
        "hello\n",
        "world\n",
    ]
    saved_name = None
    with NamedTemporaryFile(mode="wt") as f:
        f.writelines(initial_datalines)
        saved_name = f.name

    tailer = Tailer(saved_name)
    assert os.path.exists(saved_name) == False

    # if we read we shouldn't get any data
    for i in range(5):
        assert tailer.tail() is None

    # now if we write some data to the file we should see it
    # after the initial open
    with open(saved_name, "wt") as f:
        f.writelines(initial_datalines)
        f.flush()
        assert tailer.tail() is None
        assert tailer.tail() == initial_datalines
        assert tailer.tail() is None


def test_file_deleted_during_tail() -> None:
    """This tests the case where the file is deleted after we've opened it."""
    initial_datalines = [
        "Hello, world!\n",
    ]
    post_delete_datalines = [
        "Be excellent to each other.\n",
        "Party on, dudes!\n",
    ]
    f = NamedTemporaryFile(mode="wt", delete=False)
    f.writelines(initial_datalines)
    f.flush()

    tailer = Tailer(f.name)
    assert tailer.tail() == None

    # write data to deleted-but-still-open file
    os.unlink(f.name)
    f.writelines(post_delete_datalines)
    f.flush()

    # we should still get that data even though the file was deleted
    assert tailer.tail() == post_delete_datalines
