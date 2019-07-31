###############################################################

from __future__ import print_function, unicode_literals

import datetime

from django.db.models import Q

from . import conf
from .models import ImportantDate

###############################################################


def get_important_dates_queryset(startfrom_dtstart=None, upto_dtstart=None):

    days = conf.get("important_dates:days_in_advance")
    if startfrom_dtstart is None:
        today = datetime.date.today()
    else:
        today = startfrom_dtstart
    if upto_dtstart is None:
        future = today + datetime.timedelta(days=days)
    else:
        future = upto_dtstart
    qs = ImportantDate.objects.in_date_range(today, future)

    return qs


###############################################################


def important_dates(request):
    return {"important_dates": get_important_dates_queryset()}


###############################################################
