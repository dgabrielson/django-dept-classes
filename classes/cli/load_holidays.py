"""
Calculate and initialize holidays for this or the specified year.
"""
#######################
from __future__ import print_function, unicode_literals

from datetime import date

from ..utils import load_dates

#######################

DJANGO_COMMAND = "main"
USE_ARGPARSE = True
OPTION_LIST = (
    (["--year"], dict(type=int, help="Specify a year to load ")),
    (
        ["--next-year"],
        dict(
            action="store_true",
            help="Load the next years holiday.  Ignore if --year is given.",
        ),
    ),
)
HELP_TEXT = __doc__.strip()


def main(options, args):
    if "year" in options and options["year"]:
        year = options["year"]
    else:
        year = date.today().year
        if options["next_year"]:
            year += 1

    load_dates(year)
