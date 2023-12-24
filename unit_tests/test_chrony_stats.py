
#
# Copyright:    (c) 2015-2023 Paul D. Gear
# License:      AGPLv3 <http://www.gnu.org/licenses/agpl.html>

import datetime

import chrony_stats


sample_measurements = """
2021-12-30 11:28:49 17.253.66.253   N  1 111 111 1111   6  6 0.00 -3.420e-04  1.302e-03  4.121e-06  0.000e+00  1.984e-04 47505373 4B K K
2021-12-30 11:28:49 17.253.66.125   N  1 111 111 1111   6  6 0.00 -2.447e-04  1.109e-03  3.707e-06  0.000e+00  1.373e-04 47505373 4B K K
2021-12-30 11:28:49 150.101.186.50  N  2 111 111 1111   6  6 0.00 -1.287e-04  1.978e-02  4.450e-05  6.714e-04  1.282e-03 AC16FE35 4B K K
2021-12-30 11:28:49 169.254.169.123 N  3 111 111 1111   6  6 0.00 -2.082e-04  2.231e-04  1.276e-06  2.136e-04  2.747e-04 0A2C4A4E 4B K K
2021-12-30 11:28:49 150.101.186.48  N  2 111 111 1111   6  6 0.00 -4.276e-04  1.970e-02  4.405e-05  9.003e-04  6.546e-03 AC16FE35 4B K K
2021-12-30 21:38:41 169.254.169.123 N  3 111 111 1101   8  7 0.01 -1.080e-03  2.430e-03  6.257e-07  2.136e-04  2.594e-04 0A2C4A4E 4B K K
"""

sample_statistics = """
2021-12-30 11:43:02 17.253.66.253    2.762e-05 -2.951e-06  1.331e-05 -3.365e-08  1.262e-07 5.5e-02  13   0   6  0.00
2021-12-30 11:43:03 150.101.186.48   3.384e-04 -3.644e-04  1.994e-04 -8.941e-08  1.459e-06 1.4e-01  15   0   6  0.00
2021-12-30 11:44:06 169.254.169.123  3.312e-05 -1.386e-07  1.886e-05  2.105e-09  1.309e-07 3.0e-03  16   0  10  0.00
2021-12-30 11:44:06 150.101.186.50   2.934e-04 -2.109e-04  1.614e-04  2.291e-07  1.257e-06 2.2e-01  14   1   6  0.00
2021-12-30 11:44:07 17.253.66.125    2.984e-05  1.857e-05  1.568e-05  2.843e-08  1.057e-07 1.8e-01  17   0   8  0.00
2021-12-30 11:44:07 17.253.66.253    2.679e-05 -5.997e-06  1.299e-05 -3.711e-08  1.103e-07 1.3e-02  14   0   7  0.00
"""


def test_parse_measurement() -> None:
    lines = sample_measurements.split('\n')
    measurements = []
    for l in lines:
        if len(l):
            measurements.append(chrony_stats.parse_measurement(l))
    assert len(measurements) == 6

    assert measurements[0]['refid'] == '47505373' # 4th-last field extract
    assert measurements[1]['mode'] == 'server' # parse 3rd-last field
    assert measurements[2]['source'] == '150.101.186.50' # 3rd field extract
    assert measurements[3]['offset'] > measurements[4]['offset']
    assert measurements[4]['datetime'] == datetime.datetime(2021, 12, 30, 11, 28, 49, tzinfo=datetime.timezone.utc)
    assert measurements[5]['score'] == 0.01
    assert bool(measurements[5]['exceeded-max-delay-dev-ratio'])
