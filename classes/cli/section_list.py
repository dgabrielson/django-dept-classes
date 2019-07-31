"""
List sections.  
If no --term argument is given, then list current active sessions.
"""
#######################
from __future__ import print_function, unicode_literals

from django.utils.encoding import force_text

from ..models import Section

#######################
#####################################################################
#####################################################################

DJANGO_COMMAND = "main"
USE_ARGPARSE = True
OPTION_LIST = (
    (
        ["--term"],
        dict(dest="term", help="Specify a term to load, by slug (e.g., fall-2013)"),
    ),
    (
        ["--course"],
        dict(dest="course", help="Specify a course, by slug (e.g., stat-1000)"),
    ),
    (["--dept"], dict(dest="dept", help="Specify a department, by code (e.g., stat)")),
    (
        ["-f", "--fields"],
        dict(
            dest="field_list",
            help='Specify a comma delimited list of fields to include, e.g., -f "course.label,section_name,sectionschedule_set.all.0.instructor"',
        ),
    ),
)

HELP_TEXT = __doc__.strip()

#####################################################################

#####################################################################


def _resolve_lookup(object, name):
    """
    This function originally found in django.templates.base.py, modified
    for arbitrary nested field lookups from the command line -F argument.
    
    Performs resolution of a real variable (i.e. not a literal) against the
    given context.

    As indicated by the method's name, this method is an implementation
    detail and shouldn't be called by external code. Use Variable.resolve()
    instead.
    """
    current = object
    try:  # catch-all for silent variable failures
        for bit in name.split("."):
            if current is None:
                return ""
            try:  # dictionary lookup
                current = current[bit]
            except (TypeError, AttributeError, KeyError, ValueError):
                try:  # attribute lookup
                    current = getattr(current, bit)
                except (TypeError, AttributeError):
                    try:  # list-index lookup
                        current = current[int(bit)]
                    except (
                        IndexError,  # list index out of range
                        ValueError,  # invalid literal for int()
                        KeyError,  # current is a dict without `int(bit)` key
                        TypeError,
                    ):  # unsubscriptable object
                        return "Failed lookup for [{0}]".format(
                            bit
                        )  # missing attribute
            if callable(current):
                if getattr(current, "do_not_call_in_templates", False):
                    pass
                elif getattr(current, "alters_data", False):
                    current = "<< invalid -- no data alteration >>"
                else:
                    try:  # method call (assuming no args required)
                        current = current()
                    except TypeError:  # arguments *were* required
                        # GOTCHA: This will also catch any TypeError
                        # raised in the function itself.
                        current = (
                            settings.TEMPLATE_STRING_IF_INVALID
                        )  # invalid method call
    except Exception as e:
        if getattr(e, "silent_variable_failure", False):
            current = "<< invalid -- exception >>"
        else:
            raise

    return force_text(current)


#######################################################################


def main(options, args):

    qs = Section.objects.all()

    if options["term"]:
        qs = qs.filter(term__slug=options["term"])
    else:
        qs = qs.active()

    if options["course"]:
        qs = qs.filter(course__slug=options["course"])
    if options["dept"]:
        qs = qs.filter(course__department__code=options["dept"])

    for item in qs:
        value_list = [_resolve_lookup(item, "pk"), "{}".format(item)]
        if options["field_list"]:
            for field in options["field_list"].split(","):
                value_list.append(_resolve_lookup(item, field))

        print("\t".join(value_list))


#####################################################################
