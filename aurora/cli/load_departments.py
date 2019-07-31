"""
Django manage interface for populating course information from aurora/banner.
"""
#######################
from __future__ import print_function, unicode_literals

from io import StringIO

#######################
from pprint import pprint

from classes.models import Semester
from django.core.mail import EmailMessage
from django.utils.encoding import force_text

from ..utils import aurora_scrape
from ..utils.load_departments import load_departments

DJANGO_COMMAND = "main"  # enable this is a CLI command
# Metadata about this subcommand, for integration.
OPTION_LIST = (
    (["--year"], dict(dest="year", help="Specify a year to load ")),
    (
        ["--term"],
        dict(dest="term", help="Specify a term to load (fall, winter, or summer)"),
    ),
    (["--mailto"], dict(help="Send any output to this email address")),
    (
        ["--subject"],
        dict(help="Override the default subject line (only effective with --mailto)"),
    ),
)
ARGS_USAGE = "[--year YYYY --term TTTT]"
HELP_TEXT = "Populate department information from aurora/banner"


def main(options, args):

    if not options["year"] and not options["term"]:
        start_year, term_code = Semester.objects.get_next_raw_tuple()
        start_term = Semester.objects.term_code_to_name(term_code).lower()
    elif options["year"] and options["term"]:
        start_year = int(options["year"])
        start_term = options["term"]
    else:
        print("Error: must give both --year YYYY and --term TTTTT options.")
        return

    output = StringIO()
    data = aurora_scrape.fetch_department_list(start_year, start_term)
    warnings = load_departments(start_year, start_term, data)
    for w in warnings:
        if w:
            print("{}".format(w), file=output)

    if output:
        if options["mailto"]:
            subject = options["subject"] or "Aurora sync"
            email = EmailMessage(
                subject=subject, body=output.getvalue(), to=[options["mailto"]]
            )
            email.send()
        else:
            print(output.getvalue().strip())
