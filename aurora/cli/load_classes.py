"""
Django manage interface for populating course information from
aurora/banner.
"""
#########################################################################

from __future__ import print_function, unicode_literals

from io import StringIO
from pprint import pprint

from classes.models import Section, Semester
from django.core.mail import EmailMessage
from django.utils.encoding import force_text

from ..models import AuroraDepartment
from ..utils import aurora_scrape
from ..utils.load_classes import load_classes

#########################################################################
#########################################################################

DJANGO_COMMAND = "main"  # enable this is a CLI command
# Metadata about this subcommand, for integration.
USE_ARGPARSE = True
OPTION_LIST = (
    (["--year"], dict(help="Specify a year to load ")),
    (["--term"], dict(help="Specify a term to load (fall, winter, or summer)")),
    (["--mailto"], dict(help="Send any output to this email address")),
    (
        ["--subject"],
        dict(help="Override the default subject line (only effective with --mailto)"),
    ),
    (
        ["--delete"],
        dict(action="store_true", help="Delete sections when no longer available"),
    ),
)
ARGS_USAGE = "[--year YYYY --term TTTT]"
HELP_TEXT = "Populate course information from aurora/banner"

#########################################################################


def main(options, args):

    if not options["year"] and not options["term"]:
        semester_qs = Semester.objects.get_current_or_future().filter(advertised=True)
        # In winter, always pad this out to next winter...
        curr_sem = Semester.objects.get_current()
        if curr_sem.get_term_display() == "Winter":
            pk_list = []
            while True:
                curr_sem = curr_sem.get_next()
                pk_list.append(curr_sem.pk)
                if curr_sem.get_term_display() == "Winter":
                    break
            semester_qs |= Semester.objects.filter(pk__in=pk_list)

    elif options["year"] and options["term"]:
        semester_qs = [Semester.objects.get_by_pair(options["year"], options["term"])]

    else:
        print("Error: must give both --year YYYY and --term TTTTT options.")
        return

    verbosity = int(options["verbosity"])

    output = StringIO()
    aurora_sync_codes = AuroraDepartment.objects.sync_codes()
    for semester in semester_qs:
        if semester.is_current():
            p = Semester.objects.current_percent()
            if p > 0.5:
                if verbosity > 1:
                    print(
                        "** Skipping semester {} because we are {} percent through...".format(
                            semester, int(round(100 * p))
                        )
                    )
                continue
        year = semester.year
        term = semester.get_term_display().lower()
        for course_code in aurora_sync_codes:
            try:
                data = aurora_scrape.main(course_code, year, term)
            except AssertionError:
                if verbosity > 0:
                    print(
                        "No classes found for {0} {1} {2}".format(
                            course_code, year, term
                        )
                    )
            else:
                if verbosity > 2:
                    pprint(data)
                warnings = load_classes(
                    year,
                    term,
                    course_code,
                    data,
                    delete=options["delete"],
                    verbosity=verbosity,
                )
                if any(warnings.values()) and verbosity > 0:
                    print(
                        "*** Semester: {}, Department: {} ***".format(
                            semester, course_code
                        )
                    )
                # pprint(warnings)
                for section in warnings:
                    if warnings[section]:
                        print(force_text(section), file=output)
                        for warning in warnings[section]:
                            print("\t" + force_text(warning), file=output)

    if not aurora_sync_codes:
        print(
            "[!] No departments set for synchronizaition.\nAdd or update some Aurora Departments.",
            file=output,
        )

    text = output.getvalue().strip()
    if text:
        if options["mailto"]:
            subject = options["subject"] or "Aurora sync"
            email = EmailMessage(subject=subject, body=text, to=[options["mailto"]])
            email.send()
        else:
            print(text)


#########################################################################
