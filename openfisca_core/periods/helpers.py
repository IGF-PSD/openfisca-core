from typing import Dict

import datetime
import os

from . import config
from .instant_ import Instant
from .period_ import Period


def instant(instant):
    """Return a new instant, aka a triple of integers (year, month, day).

    Args:
        instant: An ``instant-like`` object.

    Returns:
        None: When ``instant`` is None.
        :obj:`.Instant`: Otherwise.

    Raises:
        :exc:`ValueError`: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> instant((2021,))
        Instant((2021, 1, 1))

        >>> instant((2021, 9))
        Instant((2021, 9, 1))

        >>> instant(datetime.date(2021, 9, 16))
        Instant((2021, 9, 16))

        >>> instant(Instant((2021, 9, 16)))
        Instant((2021, 9, 16))

        >>> instant(Period(("year", Instant((2021, 9, 16)), 1)))
        Instant((2021, 9, 16))

        >>> instant(2021)
        Instant((2021, 1, 1))

        >>> instant("2021")
        Instant((2021, 1, 1))

    """

    if instant is None:
        return None
    if isinstance(instant, Instant):
        return instant
    if isinstance(instant, str):
        if not config.INSTANT_PATTERN.match(instant):
            raise ValueError(
                "'{}' is not a valid instant. Instants are described using the 'YYYY-MM-DD' format, for instance '2015-06-15'.".format(
                    instant
                )
            )
        instant = Instant(int(fragment) for fragment in instant.split("-", 2)[:3])
    elif isinstance(instant, datetime.date):
        instant = Instant((instant.year, instant.month, instant.day))
    elif isinstance(instant, int):
        instant = (instant,)
    elif isinstance(instant, list):
        assert 1 <= len(instant) <= 3
        instant = tuple(instant)
    elif isinstance(instant, Period):
        instant = instant.start
    else:
        assert isinstance(instant, tuple), instant
        assert 1 <= len(instant) <= 3
    if len(instant) == 1:
        return Instant((instant[0], 1, 1))
    if len(instant) == 2:
        return Instant((instant[0], instant[1], 1))
    return Instant(instant)


def instant_date(instant):
    """Returns the date representation of an :class:`.Instant`.

    Args:
        instant (:obj:`.Instant`, optional):

    Returns:
        None: When ``instant`` is None.
        :obj:`datetime.date`: Otherwise.

    Examples:
        >>> instant_date(Instant((2021, 1, 1)))
        datetime.date(2021, 1, 1)

    """

    if instant is None:
        return None
    instant_date = config.date_by_instant_cache.get(instant)
    if instant_date is None:
        config.date_by_instant_cache[instant] = instant_date = datetime.date(*instant)
    return instant_date


def period(value) -> Period:
    """Return a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        :obj:`.Period`: A period.

    Raises:
        :exc:`ValueError`: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> period(Period(("year", Instant((2021, 1, 1)), 1)))
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> period(Instant((2021, 1, 1)))
        Period(('day', Instant((2021, 1, 1)), 1))

        >>> period("eternity")
        Period(('eternity', Instant((1, 1, 1)), inf))

        >>> period(2021)
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> period("2014")
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> period("year:2014")
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> period("month:2014-2")
        Period(('month', Instant((2014, 2, 1)), 1))

        >>> period("year:2014-2")
        Period(('year', Instant((2014, 2, 1)), 1))

        >>> period("day:2014-2-2")
        Period(('day', Instant((2014, 2, 2)), 1))

        >>> period("day:2014-2-2:3")
        Period(('day', Instant((2014, 2, 2)), 3))

    """

    if isinstance(value, Period):
        return value

    if isinstance(value, Instant):
        return Period((config.DAY, value, 1))

    def parse_simple_period(value):
        """Parses simple periods respecting the ISO format.

        Such as 2012 or 2015-03.

        """

        try:
            date = datetime.datetime.strptime(value, "%Y")
        except ValueError:
            try:
                date = datetime.datetime.strptime(value, "%Y-%m")
            except ValueError:
                try:
                    date = datetime.datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return None
                else:
                    return Period(
                        (config.DAY, Instant((date.year, date.month, date.day)), 1)
                    )
            else:
                return Period((config.MONTH, Instant((date.year, date.month, 1)), 1))
        else:
            return Period((config.YEAR, Instant((date.year, date.month, 1)), 1))

    def raise_error(value):
        message = os.linesep.join(
            [
                "Expected a period (eg. '2017', '2017-01', '2017-01-01', ...); got: '{}'.".format(
                    value
                ),
                "Learn more about legal period formats in OpenFisca:",
                "<https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-simulations>.",
            ]
        )
        raise ValueError(message)

    if value == "ETERNITY" or value == config.ETERNITY:
        return Period(("eternity", instant(datetime.date.min), float("inf")))

    # check the type
    if isinstance(value, int):
        return Period((config.YEAR, Instant((value, 1, 1)), 1))
    if not isinstance(value, str):
        raise_error(value)

    # try to parse as a simple period
    period = parse_simple_period(value)
    if period is not None:
        return period

    # complex period must have a ':' in their strings
    if ":" not in value:
        raise_error(value)

    components = value.split(":")

    # left-most component must be a valid unit
    unit = components[0]
    if unit not in (config.DAY, config.MONTH, config.YEAR):
        raise_error(value)

    # middle component must be a valid iso period
    base_period = parse_simple_period(components[1])
    if not base_period:
        raise_error(value)

    # period like year:2015-03 have a size of 1
    if len(components) == 2:
        size = 1
    # if provided, make sure the size is an integer
    elif len(components) == 3:
        try:
            size = int(components[2])
        except ValueError:
            raise_error(value)
    # if there is more than 2 ":" in the string, the period is invalid
    else:
        raise_error(value)

    # reject ambiguous period such as month:2014
    if unit_weight(base_period.unit) > unit_weight(unit):
        raise_error(value)

    return Period((unit, base_period.start, size))


def key_period_size(period):
    """Defines a key in order to sort periods by length.

    It uses two aspects: first, ``unit``, then, ``size``.

    Args:
        period: An :mod:`.openfisca_core` :obj:`.Period`.

    Returns:
        :obj:`str`: A string.

    Examples:
        >>> instant = Instant((2021, 9, 14))

        >>> period = Period(("day", instant, 1))
        >>> key_period_size(period)
        '100_1'

        >>> period = Period(("year", instant, 3))
        >>> key_period_size(period)
        '300_3'

    """

    unit, start, size = period

    return "{}_{}".format(unit_weight(unit), size)


def unit_weights() -> Dict[str, int]:
    """Assigns weights to date units.

    Examples:
        >>> unit_weights()
        {<DateUnit.DAY: 'day'>: 100...}

    """

    return {
        config.DAY: 100,
        config.MONTH: 200,
        config.YEAR: 300,
        config.ETERNITY: 400,
    }


def unit_weight(unit: str) -> int:
    return unit_weights()[unit]
