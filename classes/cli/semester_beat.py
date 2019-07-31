"""
Semester Beat is a daily cron job which determines which
semesters should be advertised.
Use this when you do not want to manually manage which 
semesters are "viewable".

This logic is controlled by the 'semester:advertisement_rules'
configuration setting.
"""
################################################################
from __future__ import print_function, unicode_literals

from datetime import date, timedelta

from .. import conf
from ..models import Semester

################################################################

DJANGO_COMMAND = "main"
USE_ARGPARSE = True
OPTION_LIST = (
    (
        ["--no-save"],
        dict(action="store_true", help="Do not actually update the database."),
    ),
)
HELP_TEXT = __doc__.strip()

################################################################

################################################################


def set_advertised(semester, no_save, verbosity):
    if not semester.advertised:
        semester.advertised = True
        if no_save or verbosity > 0:
            print("* {0} now advertised".format(semester))
        if not no_save:
            semester.save()


################################################################


def clear_advertised(semester, no_save, verbosity):
    if semester.advertised:
        semester.advertised = False
        if no_save or verbosity > 0:
            print(" * {0} no longer advertised".format(semester))
        if not no_save:
            semester.save()


################################################################


def main(options, args):
    """ 
    """
    no_save = options["no_save"]
    verbosity = int(options["verbosity"])
    rules = conf.get("semester:advertisement_rules")
    today = date.today()
    # Note that this implementation relies on the ordering of Semester objects.
    set_next = 0
    for semester in Semester.objects.all():
        if verbosity > 2:
            print("semester = {}".format(semester))
        start, end = semester.get_start_finish_dates()
        start_grace = start - timedelta(
            days=rules["in_advance_days"].get(semester.term, 0)
        )
        end_grace = end + timedelta(days=rules["grace_period"].get(semester.term, 0))
        if verbosity > 2:
            print("start, end = ({}, {})".format(start, end))
            print("start_grace, end_grace = ({}, {})".format(start_grace, end_grace))

        # past
        if end_grace < today:
            clear_advertised(semester, no_save, verbosity)

        # current
        if start_grace <= today <= end_grace:
            set_advertised(semester, no_save, verbosity)
            set_next = rules["next"][semester.term]
            if verbosity > 2:
                print("set_next = {}".format(set_next))

        # future
        if today < start_grace:
            if set_next > 0:
                set_advertised(semester, no_save, verbosity)
                set_next -= 1
            else:
                clear_advertised(semester, no_save, verbosity)

    while set_next > 0:
        # this means that there are semesters which *should* be advertised
        #   but do not yet exist, so create them.
        semester = semester.get_next()
        set_advertised(semester, no_save, verbosity)
        set_next -= 1

    if verbosity > 1:
        semester_list = Semester.objects.advertised()
        plural = "s" if len(semester_list) == 1 else ""
        print("Advertised semester{0}:".format(plural))
        for semester in semester_list:
            print("* {0}".format(semester))


################################################################
