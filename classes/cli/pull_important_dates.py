"""
Pull future important dates from another installation using the API.
"""
#######################
from __future__ import print_function, unicode_literals

import json
from pprint import pprint

from .. import conf
from ..models import ImportantDate

#######################

try:
    # Python 3:
    from urllib.request import urlopen
except ImportError:
    # Python 2:
    from urllib2 import urlopen

DJANGO_COMMAND = "main"
USE_ARGPARSE = True
OPTION_LIST = (
    (
        ["--api-url"],
        dict(
            dest="api_url",
            help='Specify an API url, if not given, the config option "api:important_dates_src_url" will be used',
        ),
    ),
)
HELP_TEXT = __doc__.strip()


def load_important_date_from_dict(data, blacklist_fields=["id", "created", "modified"]):
    """
    The data dictionary is from a JSON dump of the ImportantDate fields.
    """
    for f in blacklist_fields:  # don't use these
        if f in data:
            del data[f]

    obj, created = ImportantDate.objects.get_or_create(**data)
    if created:
        print(obj)


def main(options, args):

    if "api_url" in options and options["api_url"]:
        api_url = options["api_url"]
    else:
        api_url = conf.get("api:important_dates_src_url")

    if api_url:
        text_b = urlopen(api_url).read()
        text = text_b.decode("utf-8")
        data = json.loads(text)
        for record in data:
            load_important_date_from_dict(record)
    else:
        print(
            "[!!!]",
            'No API url is set.  Either set "api:important_dates_src_url" in the config dictionary or give --api-url',
        )
