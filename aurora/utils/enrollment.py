#######################
from __future__ import print_function, unicode_literals

from . import aurora_scrape

#######################


def get_enrollment(section):
    """get_enrollment(section) -> int, int, int

    Returns the (capacity, enrollment, available) numbers for this section

    WARNING: this function always pulls live numbers from aurora,
    avoid using directly in views or templates.
    """
    crn = section.crn
    year = section.term.year
    term = section.term.get_term_display().lower()

    return aurora_scrape.enrollment_info(crn, year, term)
