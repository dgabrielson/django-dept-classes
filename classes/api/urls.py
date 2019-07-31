"""
Url patterns for the classes api.
"""
#######################
from __future__ import print_function, unicode_literals

from django.conf.urls import url

from .views import important_dates_all, important_dates_detail, important_dates_future

#######################

urlpatterns = [
    url(
        r"^important-dates/all/$",
        important_dates_all,
        name="classes-api-important-dates-all",
    ),
    url(
        r"^important-dates/future/$",
        important_dates_future,
        name="classes-api-important-dates-future",
    ),
    url(
        r"^important-dates/(?P<pk>\d+)/$",
        important_dates_detail,
        name="classes-api-important-dates-detail",
    ),
]
