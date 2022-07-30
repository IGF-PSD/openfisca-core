import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period


@pytest.mark.parametrize(
    "arg, expected",
    [
        ["eternity", Period((DateUnit.ETERNITY, Instant((1, 1, 1)), float("inf")))],
        ["ETERNITY", Period((DateUnit.ETERNITY, Instant((1, 1, 1)), float("inf")))],
        [
            DateUnit.ETERNITY,
            Period((DateUnit.ETERNITY, Instant((1, 1, 1)), float("inf"))),
        ],
        [datetime.date(1, 1, 1), Period((DateUnit.DAY, Instant((1, 1, 1)), 1))],
        [Instant((1, 1, 1)), Period((DateUnit.DAY, Instant((1, 1, 1)), 1))],
        [
            Period((DateUnit.DAY, Instant((1, 1, 1)), 365)),
            Period((DateUnit.DAY, Instant((1, 1, 1)), 365)),
        ],
        [-1, Period((DateUnit.YEAR, Instant((-1, 1, 1)), 1))],
        [0, Period((DateUnit.YEAR, Instant((0, 1, 1)), 1))],
        [1, Period((DateUnit.YEAR, Instant((1, 1, 1)), 1))],
        [999, Period((DateUnit.YEAR, Instant((999, 1, 1)), 1))],
        [1000, Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["1000", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["1000-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
        ["1000-01-01", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
        ["1004-02-29", Period((DateUnit.DAY, Instant((1004, 2, 29)), 1))],
        ["1000-W01", Period((DateUnit.WEEK, Instant((999, 12, 30)), 1))],
        ["1000-W01-1", Period((DateUnit.WEEKDAY, Instant((999, 12, 30)), 1))],
        ["year:1000", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["year:1000-01", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["year:1000-01-01", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["year:1000-W01", Period((DateUnit.YEAR, Instant((999, 12, 30)), 1))],
        ["year:1000-W01-1", Period((DateUnit.YEAR, Instant((999, 12, 30)), 1))],
        ["year:1000:1", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["year:1000-01:1", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["year:1000-01-01:1", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
        ["year:1000-W01:1", Period((DateUnit.YEAR, Instant((999, 12, 30)), 1))],
        ["year:1000-W01-1:1", Period((DateUnit.YEAR, Instant((999, 12, 30)), 1))],
        ["year:1000:3", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 3))],
        ["year:1000-01:3", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 3))],
        ["year:1000-01-01:3", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 3))],
        ["year:1000-W01:3", Period((DateUnit.YEAR, Instant((999, 12, 30)), 3))],
        ["year:1000-W01-1:3", Period((DateUnit.YEAR, Instant((999, 12, 30)), 3))],
        ["month:1000-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
        ["month:1000-01-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
        ["week:1000-W01", Period((DateUnit.WEEK, Instant((999, 12, 30)), 1))],
        ["week:1000-W01-1", Period((DateUnit.WEEK, Instant((999, 12, 30)), 1))],
        ["month:1000-01:1", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
        ["month:1000-01:3", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 3))],
        ["month:1000-01-01:3", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 3))],
        ["week:1000-W01:1", Period((DateUnit.WEEK, Instant((999, 12, 30)), 1))],
        ["week:1000-W01:3", Period((DateUnit.WEEK, Instant((999, 12, 30)), 3))],
        ["week:1000-W01-1:3", Period((DateUnit.WEEK, Instant((999, 12, 30)), 3))],
        ["day:1000-01-01", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
        ["day:1000-01-01:3", Period((DateUnit.DAY, Instant((1000, 1, 1)), 3))],
        ["weekday:1000-W01-1", Period((DateUnit.WEEKDAY, Instant((999, 12, 30)), 1))],
        ["weekday:1000-W01-1:3", Period((DateUnit.WEEKDAY, Instant((999, 12, 30)), 3))],
    ],
)
def test_period(arg, expected):
    assert periods.period(arg) == expected


@pytest.mark.parametrize(
    "arg, error",
    [
        [None, ValueError],
        [DateUnit.YEAR, ValueError],
        ["1", ValueError],
        ["999", ValueError],
        ["1000-0", ValueError],
        ["1000-13", ValueError],
        ["1000-W0", ValueError],
        ["1000-W54", ValueError],
        ["1000-0-0", ValueError],
        ["1000-1-0", ValueError],
        ["1000-2-31", ValueError],
        ["1000-W0-0", ValueError],
        ["1000-W1-0", ValueError],
        ["1000-W1-8", ValueError],
        ["a", ValueError],
        ["year", ValueError],
        ["1:1000", ValueError],
        ["a:1000", ValueError],
        ["month:1000", ValueError],
        ["week:1000", ValueError],
        ["day:1000-01", ValueError],
        ["weekday:1000-W1", ValueError],
        ["1000:a", ValueError],
        ["1000:1", ValueError],
        ["1000-01:1", ValueError],
        ["1000-01-01:1", ValueError],
        ["1000-W1:1", ValueError],
        ["1000-W1-1:1", ValueError],
        ["month:1000:1", ValueError],
        ["week:1000:1", ValueError],
        ["day:1000:1", ValueError],
        ["day:1000-01:1", ValueError],
        ["weekday:1000:1", ValueError],
        ["weekday:1000-W1:1", ValueError],
        [(), ValueError],
        [{}, ValueError],
        ["", ValueError],
        [(None,), ValueError],
        [(None, None), ValueError],
        [(None, None, None), ValueError],
        [(None, None, None, None), ValueError],
        [(Instant((1, 1, 1)),), ValueError],
        [(Period((DateUnit.DAY, Instant((1, 1, 1)), 365)),), ValueError],
        [(1,), ValueError],
        [(1, 1), ValueError],
        [(1, 1, 1), ValueError],
        [(-1,), ValueError],
        [(-1, -1), ValueError],
        [(-1, -1, -1), ValueError],
        [("-1",), ValueError],
        [("-1", "-1"), ValueError],
        [("-1", "-1", "-1"), ValueError],
        [("1-1",), ValueError],
        [("1-1-1",), ValueError],
    ],
)
def test_period_with_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.period(arg)
