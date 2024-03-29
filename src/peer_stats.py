# Extract and parse chronyd measurements and ntpd peerstats
#
# Copyright:    (c) 2016-2024 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import datetime
import re
import sys
from typing import List


leapcodes = {
    "N": 0,
    "+": 1,
    "-": 2,
    "?": 3,
}

modes = {
    "1": "active peer",
    "2": "passive peer",
    "4": "server",
}

timestamp_sources = {
    "D": "daemon",
    "H": "hardware",
    "K": "kernel",
}


def checkfail(test: str) -> int:
    """Reverse the polarity of the tests so that 1 asserts the error.
    This is to make it more natural to write queries asserting, e.g. that a packet is a duplicate."""
    return 1 if test == "0" else 0


skiplines = r"^===|^ *Date"
regex = re.compile(skiplines)


# From chrony.conf measurements.log docs:
# The columns are as follows (the quantities in square brackets are the values from the example line above):
# 1. Date [2015-10-13]
# 2. Hour:Minute:Second. Note that the date-time pair is expressed in UTC, not the local time zone. [05:40:50]
# 3. IP address of server or peer from which measurement came [203.0.113.15]
# 4. Leap status (N means normal, + means that the last minute of the current month has 61 seconds, - means that the last minute of the month has 59 seconds,
#    ? means the remote computer is not currently synchronised.) [N]
# 5. Stratum of remote computer. [2]
# 6. RFC 5905 tests 1 through 3 (1=pass, 0=fail) [111]
# 7. RFC 5905 tests 5 through 7 (1=pass, 0=fail) [111]
# 8. Tests for maximum delay, maximum delay ratio and maximum delay dev ratio, against defined parameters, and a test for synchronisation loop (1=pass, 0=fail) [1111]
# 9. Local poll [10]
# 10. Remote poll [10]
# 11. ‘Score’ (an internal score within each polling level used to decide when to increase or decrease the polling level. This is adjusted based on number of measurements currently
#     being used for the regression algorithm). [1.0]
# 12. The estimated local clock error (theta in RFC 5905). Positive indicates that the local clock is slow of the remote source. [-4.966e-03]
# 13. The peer delay (delta in RFC 5905). [2.296e-01]
# 14. The peer dispersion (epsilon in RFC 5905). [1.577e-05]
# 15. The root delay (DELTA in RFC 5905). [1.615e-01]
# 16. The root dispersion (EPSILON in RFC 5905). [7.446e-03]
# 17. Reference ID of the server’s source as a hexadecimal number. [CB00717B]
# 18. NTP mode of the received packet (1=active peer, 2=passive peer, 4=server, B=basic, I=interleaved). [4B]
# 19. Source of the local transmit timestamp (D=daemon, K=kernel, H=hardware). [D]
# 20. Source of the local receive timestamp (D=daemon, K=kernel, H=hardware). [K]


def extract_chrony_measurements(f: List[str]) -> dict:
    return {
        # sorted by field position rather than name
        "timestamp_ns": str_to_nanoseconds(f[0], f[1]),
        "source": f[2],
        "leap": leapcodes[f[3]],
        "stratum": int(f[4]),
        "duplicate": checkfail(f[5][0]),
        "bogus": checkfail(f[5][1]),
        "invalid": checkfail(f[5][2]),
        "authentication_fail": checkfail(f[6][0]),
        "synchronized": int(f[6][1]),
        "bad_header": checkfail(f[6][2]),
        "exceeded_max_delay": checkfail(f[7][0]),
        "exceeded_max_delay_ratio": checkfail(f[7][1]),
        "exceeded_max_delay_dev_ratio": checkfail(f[7][2]),
        "sync_loop": checkfail(f[7][3]),
        "local_poll": int(f[8]),
        "remote_poll": int(f[9]),
        "score": float(f[10]),
        "offset": float(f[11]),
        "delay": float(f[12]),
        "dispersion": float(f[13]),
        "root_delay": float(f[14]),
        "root_dispersion": float(f[15]),
        "refid": f[16],
        "mode": modes.get(f[17][0], "UNKNOWN"),
        "interleaved": 1 if f[17][1] == "I" else 0,
        "tx_timestamp": timestamp_sources.get(f[18], "UNKNOWN"),
        "rx_timestamp": timestamp_sources.get(f[19], "UNKNOWN"),
    }


# Chrony statistics docs
# 1. Date [2015-07-22]
# 2. Hour:Minute:Second. Note that the date-time pair is expressed in UTC, not the local time zone. [05:40:50]
# 3. IP address of server or peer from which measurement comes [203.0.113.15]
# 4. The estimated standard deviation of the measurements from the source (in seconds). [6.261e-03]
# 5. The estimated offset of the source (in seconds, positive means the local clock is estimated to be fast, in this case). [-3.247e-03]
# 6. The estimated standard deviation of the offset estimate (in seconds). [2.220e-03]
# 7. The estimated rate at which the local clock is gaining or losing time relative to the source (in seconds per second, positive means the local clock is gaining). This is relative to
#     the compensation currently being applied to the local clock, not to the local clock without any compensation. [1.874e-06]
# 8. The estimated error in the rate value (in seconds per second). [1.080e-06].
# 9. The ratio of |old_rate - new_rate| / old_rate_error. Large values indicate the statistics are not modelling the source very well. [7.8e-02]
# 10. The number of measurements currently being used for the regression algorithm. [16]
# 11. The new starting index (the oldest sample has index 0; this is the method used to prune old samples when it no longer looks like the measurements fit a linear model). [0, i.e. no
#     samples discarded this time]
# 12. The number of runs. The number of runs of regression residuals with the same sign is computed. If this is too small it indicates that the measurements are no longer represented
#     well by a linear model and that some older samples need to be discarded. The number of runs for the data that is being retained is tabulated. Values of approximately half the
#     number of samples are expected. [8]
# 13. The estimated or configured asymmetry of network jitter on the path to the source which was used to correct the measured offsets. The asymmetry can be between -0.5 and +0.5. A
#     negative value means the delay of packets sent to the source is more variable than the delay of packets sent from the source back. [0.00, i.e. no correction for asymmetry]


def extract_chrony_statistics(f: List[str]) -> dict:
    return {
        # sort by field position rather than name
        "timestamp_ns": str_to_nanoseconds(f[0], f[1]),
        "source": f[2],
        "stdev": float(f[3]),
        "offset": float(f[4]),
        "stdev_est": float(f[5]),
        "skew": float(f[6]),
        "freq": float(f[7]),
        "stress": float(f[8]),
        "samples": int(f[9]),
        "begin_sample": int(f[10]),
        "runs": int(f[11]),
        "asymmetry": float(f[12]),
    }


# Chrony tracking docs:
# 1. Date [2017-08-22]
# 2. Hour:Minute:Second. Note that the date-time pair is expressed in UTC, not the local time zone. [13:22:36]
# 3. The IP address of the server or peer to which the local system is synchronised. [203.0.113.15]
# 4. The stratum of the local system. [2]
# 5. The local system frequency (in ppm, positive means the local system runs fast of UTC). [-3.541]
# 6. The error bounds on the frequency (in ppm). [0.075]
# 7. The estimated local offset at the epoch, which is normally corrected by slewing the local clock (in seconds, positive indicates the clock is fast of UTC). [-8.621e-06]
# 8. Leap status (N means normal, + means that the last minute of this month has 61 seconds, - means that the last minute of the month has 59 seconds, ? means the clock is not currently
#     synchronised.) [N]
# 9. The number of combined sources. [2]
# 10. The estimated standard deviation of the combined offset (in seconds). [2.940e-03]
# 11. The remaining offset correction from the previous update (in seconds, positive means the system clock is slow of UTC). [-2.084e-04]
# 12. The total of the network path delays to the reference clock to which the local clock is ultimately synchronised (in seconds). [1.534e-02]
# 13. The total dispersion accumulated through all the servers back to the reference clock to which the local clock is ultimately synchronised (in seconds). [3.472e-04]
# 14. The maximum estimated error of the system clock in the interval since the previous update (in seconds). It includes the offset, remaining offset correction, root delay, and
#     dispersion from the previous update with the dispersion which accumulated in the interval. [8.304e-03]


def extract_chrony_tracking(f: List[str]) -> dict:
    return {
        # sort by field position rather than name
        "timestamp_ns": str_to_nanoseconds(f[0], f[1]),
        "source": f[2],
        "stratum": int(f[3]),
        "freq": float(f[4]),
        "skew": float(f[5]),
        "offset": float(f[6]),
        "leap": leapcodes.get(f[7], -1),
        "num_combined": int(f[8]),
        "stdev": float(f[9]),
        "remaining_correction": float(f[10]),
        "root_delay": float(f[11]),
        "root_dispersion": float(f[12]),
        "max_error": float(f[13]),
    }


# Ref: https://www.ntp.org/documentation/4.2.8-series/monopt/

# 48773 	MJD 	date
# 10847.650 	s 	time past midnight
# 127.127.4.1 	IP 	source address
# 9714 	hex 	status word
# -0.001605376 	s 	clock offset
# 0.000000000 	s 	roundtrip delay
# 0.001424877 	s 	dispersion
# 0.000958674 	s 	RMS jitter


def extract_ntp_peerstats(f: List[str]) -> dict:
    basefields = {
        # sorted by field position rather than name
        "timestamp_ns": mjd_to_nanoseconds(float(f[0]), float(f[1])),
        "source": f[2],
        "offset": float(f[4]),
        "delay": float(f[5]),
        "dispersion": float(f[6]),
        "jitter": float(f[7]),
    }
    basefields.update(extract_ntpd_status_word(f[3]))
    return basefields


select_field = {
    0: "invalid",
    1: "false",
    2: "excess",
    3: "outlier",
    4: "survivor",
    5: "backup",
    6: "sync",
    7: "pps",
}

# Ref: https://www.ntp.org/documentation/4.2.8-series/decode/#peer-status-word


def extract_ntpd_status_word(status: str) -> dict:
    status_word = int(status, 16) >> 8
    return {
        # ordered from most significant to least significant bits
        "persistent": bool(status_word & 0x80),
        "authentication_enabled": bool(status_word & 0x40),
        "authenticated": bool(status_word & 0x20),
        "reachable": bool(status_word & 0x10),
        "broadcast": bool(status_word & 0x08),
        "peertype": select_field[status_word & 0x07],
    }


def mjd_to_nanoseconds(day: float, time: float) -> int:
    """Convert mean julian day + time into nanoseconds since the epoch"""
    return int(((day - 40587) * 86400 + time) * 1_000_000_000)


def parse_measurement(line: str) -> dict:
    if regex.match(line):
        return None
    try:
        fields = line.split()
        if len(fields) == 20:
            return extract_chrony_measurements(fields)
        elif len(fields) == 8:
            return extract_ntp_peerstats(fields)
        else:
            return None
    except Exception as e:
        print(e, file=sys.stderr)
        return None


def str_to_nanoseconds(date: str, time: str) -> int:
    """Convert date + time strings in UTC to nanoseconds since the epoch"""
    return int(datetime.datetime.fromisoformat("+".join((date, time, "00:00"))).timestamp() * 1_000_000_000)
