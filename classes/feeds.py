#######################
from __future__ import print_function, unicode_literals

import datetime

from classes.models import ImportantDate
from django.contrib.syndication.views import Feed

#######################


class ImportantDatesFeed(Feed):
    title = "Important Dates"
    link = "/classes/calendar/important-dates"
    description = "Important Dates"
    title_template = "feeds/important-dates_title.html"
    description_template = "feeds/important-dates_description.html"

    def items(self):
        threshold = datetime.date.today() + datetime.timedelta(days=7)
        return ImportantDate.objects.before(threshold).order_by("-date")[:5]

    def item_pubdate(self, item):
        # this return value needs to be a datetime-compatible field, i.e., a models.DateTimeField
        return item.modified

    def item_link(self, item):
        return ""  # or provide ImportantDate with get_absolute_url() method.


#
