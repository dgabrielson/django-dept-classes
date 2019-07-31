"""
Instructor Beat is a daily cron job which determines if
instructors need to be promoted from a section schedule to
a section.
Use this when you do not want to manually manage instructors
for sections.
"""
################################################################

from __future__ import print_function, unicode_literals

from ..models import Section

################################################################

DJANGO_COMMAND = "main"
USE_ARGPARSE = True
OPTION_LIST = (
    (
        ["--no-save"],
        dict(action="store_true", help="Do not actually update the database."),
    ),
    (
        ["--all"],
        dict(action="store_true", help="Do all semesters, not just advertised ones."),
    ),
)
HELP_TEXT = __doc__.strip()

################################################################

################################################################


def main(options, args):
    """
    """
    no_save = options["no_save"]
    verbosity = int(options["verbosity"])
    do_all = options["all"]

    queryset = Section.objects.all()
    if not do_all:
        queryset = queryset.filter(term__advertised=True)

    for section in queryset.iterator():
        update = False
        msg = ""
        if section.override_instructor:
            msg = "not updating due to instructor override"
        else:
            sched_instructor = section.sectionschedule_set.active().instructor()
            if sched_instructor is None:
                sched_instructor = (
                    section.sectionschedule_set.active()
                    .filter(type__name__in=["Lecture"])
                    .instructor()
                )
            if section.instructor != sched_instructor:
                section.instructor = sched_instructor
                msg = "updated instructor to {0}".format(sched_instructor)
                update = True
            else:
                msg = "instructor not updated"

            sched_addl_instr = (
                section.sectionschedule_set.active().additional_instructors()
            )
            if not sched_addl_instr:
                sched_addl_instr = (
                    section.sectionschedule_set.active()
                    .filter(type__name__in=["Lecture"])
                    .additional_instructors()
                )
            if set(section.additional_instructors.all()) != sched_addl_instr:
                if not no_save:
                    section.additional_instructors.set(sched_addl_instr)
                if sched_addl_instr:
                    s = ", ".join([str(p) for p in sched_addl_instr])
                    msg += "; updated additional_instructors to {}".format(s)
            else:
                msg += "; additional_instructors not updated"
        if no_save:
            msg += " (not saved)"
        else:
            section.save()
        if (verbosity in [1, 2] and update) or (verbosity > 2):
            print("{0}, {1} : {2}".format(section.term, section, msg))


################################################################
