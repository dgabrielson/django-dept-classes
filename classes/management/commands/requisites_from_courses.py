#######################################################################
#######################
from __future__ import print_function, unicode_literals

from django.core.management.base import BaseCommand, CommandError

from ...models import Course, Requisite

#######################
## https://docs.djangoproject.com/en/dev/howto/custom-management-commands/
################################################################

#######################################################################

#######################################################################


class Command(BaseCommand):
    help = "Ensure that each course (for advertised departements) has a corresponding requisite"

    # def add_arguments(self, parser):
    #     """
    #     Add arguments to the command.
    #     """
    #     parser.add_argument('-f', '--fields',
    #                 dest='field_list',
    #                 help='Specify a comma delimited list of fields to include, e.g., -f "course.label,section_name,sectionschedule_set.all.0.instructor"',
    #                 )

    # When you are using management commands and wish to provide console output,
    # you should write to self.stdout and self.stderr, instead of printing to
    # stdout and stderr directly. By using these proxies, it becomes much easier
    # to test your custom command. Note also that you don't need to end messages
    # with a newline character, it will be added automatically, unless you
    # specify the ``ending`` parameter to write()
    def handle(self, *args, **options):
        """
        Do the thing!
        """
        qs = Course.objects.filter(
            active=True, department__active=True, department__advertised=True
        )
        for course in qs:
            req, created = Requisite.objects.get_or_create(course=course)
            if options["verbosity"] > 0 and created:
                self.stdout.write(self.style.SUCCESS("created: {}".format(req)))
            if options["verbosity"] > 1 and not created:
                self.stdout.write(self.style.SUCCESS("already exists: {}".format(req)))
            # self.stdout.write()


#######################################################################
