#!/usr/bin/env python
#######################
from __future__ import print_function, unicode_literals

import datetime

import dateutil
import dateutil.easter
import dateutil.relativedelta

#######################


def holidays(year):
    """
    Return a list of datetime.date's, and descriptions of all the holidays in a year.
    """
    result = []

    base = datetime.date(year, 1, 1)

    result.append((base, "New Year's Day"))
    result.append(
        (
            base
            + dateutil.relativedelta.relativedelta(
                month=2, weekday=dateutil.relativedelta.MO(+3)
            ),
            "Louis Riel Day",
        )
    )
    result.append(
        (dateutil.easter.easter(year) - datetime.timedelta(days=2), "Good Friday")
    )
    # result.append((dateutil.easter.easter(year), "Easter Sunday"))
    result.append(
        (
            base
            + dateutil.relativedelta.relativedelta(
                month=5, day=24, weekday=dateutil.relativedelta.MO(-1)
            ),
            "Victoria Day",
        )
    )
    result.append(
        (base + dateutil.relativedelta.relativedelta(month=7, day=1), "Canada Day")
    )
    result.append(
        (
            base
            + dateutil.relativedelta.relativedelta(
                month=8, weekday=dateutil.relativedelta.MO(1)
            ),
            "Terry Fox Day",
        )
    )
    result.append(
        (
            base
            + dateutil.relativedelta.relativedelta(
                month=9, weekday=dateutil.relativedelta.MO(1)
            ),
            "Labour Day",
        )
    )
    result.append(
        (
            base
            + dateutil.relativedelta.relativedelta(
                month=10, weekday=dateutil.relativedelta.MO(2)
            ),
            "Thanksgiving Day",
        )
    )
    result.append(
        (
            base + dateutil.relativedelta.relativedelta(month=11, day=11),
            "Remembrance Day",
        )
    )
    result.append(
        (base + dateutil.relativedelta.relativedelta(month=12, day=25), "Christmas Day")
    )

    return result


def special_days(year):
    result = []
    base = datetime.date(year, 1, 1)

    # federal holidays
    result.append(
        (dateutil.easter.easter(year) + datetime.timedelta(days=1), "Easter Monday")
    )
    result.append(
        (base + dateutil.relativedelta.relativedelta(month=12, day=24), "Christmas Eve")
    )
    result.append(
        (base + dateutil.relativedelta.relativedelta(month=12, day=26), "Boxing Day")
    )

    # other holidays
    result.append(
        (
            base + dateutil.relativedelta.relativedelta(month=3, day=17),
            "St. Patrick's Day",
        )
    )
    result.append(
        (
            base + dateutil.relativedelta.relativedelta(month=2, day=14),
            "Valentine's Day",
        )
    )
    result.append(
        (
            base
            + dateutil.relativedelta.relativedelta(
                month=5, weekday=dateutil.relativedelta.SU(2)
            ),
            "Mother's Day",
        )
    )
    result.append(
        (
            base
            + dateutil.relativedelta.relativedelta(
                month=6, weekday=dateutil.relativedelta.SU(3)
            ),
            "Father's Day",
        )
    )
    result.append(
        (base + dateutil.relativedelta.relativedelta(month=10, day=31), "Halloween")
    )
    result.append(
        (
            base + dateutil.relativedelta.relativedelta(month=12, day=31),
            "New Year's Eve",
        )
    )
    return result


if __name__ == "__main__":
    year = datetime.date.today().year
    days = holidays(year) + special_days(year)
    days.sort()
    for dt, msg in days:
        print(dt, msg)
