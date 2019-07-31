"""
Update enrollment information for classes.
Note that this always creates new enrollment records.
"""
#######################
from __future__ import print_function, unicode_literals

import time

from classes.models import Enrollment, Section, Semester

from ..utils.enrollment import get_enrollment

#######################

DJANGO_COMMAND = "main"
OPTION_LIST = ()
USE_ARGPARSE = True
HELP_TEXT = __doc__.strip()


def main(options, args):
    verbosity = int(options.get("verbosity"))
    term_list = Semester.objects.advertised()
    for term in term_list:
        for section in term.section_set.advertised():
            result = get_enrollment(section)
            if not result:
                if verbosity >= 1:
                    print(
                        "No enrollment info for {section} [{section.term}]".format(
                            section=section
                        )
                    )
                continue

            capacity, actual, remaining, waitlist_cap, waitlist_actual, waitlist_remain = (
                result
            )
            if verbosity > 2:
                print(
                    "{0}: enrollment (cap/act/rem): {1}/{2}/{3}; waitlist: (cap/act/remain): {4}/{5}/{6}".format(
                        section, *result
                    )
                )
            Enrollment.objects.create(
                section=section,
                capacity=capacity,
                registration=actual,
                waitlist_capacity=waitlist_cap,
                waitlist_registration=waitlist_actual,
            )
            time.sleep(0.1)


#
