"""
Django manage interface for populating course information from aurora/banner.
"""
#########################################################################
#######################
from __future__ import print_function, unicode_literals

from ..models import AuroraDepartment
from ..utils import aurora_scrape

#######################

#########################################################################

DJANGO_COMMAND = "main"  # enable this is a CLI command
USE_ARGPARSE = True
OPTION_LIST = (
    (
        ["--no-save"],
        {"action": "store_true", "help": "Print changes, do not commit to database"},
    ),
    (["dept"], {"nargs": "*", "help": "Department code(s) to synchronize"}),
)
HELP_TEXT = "Update course descriptions from aurora/banner"

#########################################################################


def main(options, args):
    args = options["dept"]
    verbosity = int(options["verbosity"])

    if args:
        dept_list = AuroraDepartment.objects.filter(department_code__in=args)
    else:
        dept_list = AuroraDepartment.objects.synchronize()

    for dept in dept_list:
        for course in dept.department.course_set.active():
            if verbosity > 0:
                print(course, end=" ")
            desc = aurora_scrape.fetch_catalog_entry_by_course(
                dept.department_code, course.code
            )
            if verbosity > 2:
                print(desc)
            if course.description != desc:
                if verbosity > 1:
                    print("[updated]", end=" ")
                course.description = desc
                if not options["no_save"]:
                    course.save()
            else:
                if verbosity > 1:
                    print("[no change]", end=" ")
            print()


#########################################################################
