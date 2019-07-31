# -*- coding: utf-8 -*-
#
# NOTE: cannot import from classes.models b/c classes.models imports this file.
#######################
from __future__ import print_function, unicode_literals

import datetime

from django.utils.timezone import make_aware

from . import holidays

#######################


def unique_courses(sections):
    # Order preserving
    # source [2009-Oct-21] http://www.peterbe.com/plog/uniqifiers-benchmark
    seen = set()
    return [
        x.course
        for x in sections
        if x.course.id not in seen and not seen.add(x.course.id)
    ]


def find_section(**search_terms):
    """
    Use Section.objects.find() instead!
    """
    from classes.models import Section

    return Section.objects.find(**search_terms)


def load_dates(year):
    from classes.models import ImportantDate

    for dt, desc in holidays.holidays(year):
        if desc in ["New Year's Day", "Christmas Day"]:
            # skip these... the university is closed anyhow.
            continue
        impdate, created = ImportantDate.objects.get_or_create(
            date=dt, title=desc, no_class=True, university_closed=True
        )
        if desc == "Louis Riel Day":
            # add reading week also
            impdate, created = ImportantDate.objects.get_or_create(
                date=dt,
                end_date=dt + datetime.timedelta(days=4),
                title="Reading Week",
                no_class=True,
            )
        if desc == "Thanksgiving Day":
            # also create fall break
            impdate, created = ImportantDate.objects.get_or_create(
                date=dt - datetime.timedelta(days=4),
                end_date=dt - datetime.timedelta(days=3),
                title="Fall Term break",
                no_class=True,
            )
    # do NOT load holidays.special_days(year)


def blend_date_and_time(d, t):
    return make_aware(
        datetime.datetime(
            d.year, d.month, d.day, t.hour, t.minute, t.second, t.microsecond
        )
    )


##
