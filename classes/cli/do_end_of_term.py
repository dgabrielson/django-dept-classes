#!/usr/bin/env python
"""
This script is run 4 times per year, at the very beginning of each term.
Its purpose is to expire old data so the new term can begin cleanly.

This script is designed to be run via a CRON script, and MUST be run
from the apps directory.

0 1 1 jan * cd /www/websites/neyman01/django/apps ; python END_OF_TERM_master.py
0 1 1 may * cd /www/websites/neyman01/django/apps ; python END_OF_TERM_master.py
0 1 1 sep * cd /www/websites/neyman01/django/apps ; python END_OF_TERM_master.py

----------------------

This will scan all apps for a utils/END_OF_TERM.py module.
If found, this module will be loaded (utils/__init__.py must exist!)
and its main() function executed.

It is crucial that these END_OF_TERM modules not rely on any active
status outside their own applications, since things may have been
decativated earlier in the run.

MOST of the END_OF_TERM scripts start like this:

    for semester in Semester.objects.all():
        if semester.is_current():
            continue
        for object in Foobar.objects.filter(Term=semester):
            [...]


"""
#######################
from __future__ import print_function, unicode_literals

import os
import sys
import traceback

from django.conf import settings

#######################
############################################################################

# Setup Django environment
DJANGO_COMMAND = "main"
OPTION_LIST = ()
HELP_TEXT = "Do end of term cleanup (cron)."

############################################################################


def main(options, args):
    for app in settings.INSTALLED_APPS:
        print("=" * 50)
        print("APPLICATION: {!r}".format(app))
        try:
            m = __import__("%s.utils.END_OF_TERM" % app)
        except ImportError:
            print("  - no end of term cleanup for this app -")
            # pass    # no end of term cleanup for this app
        else:
            try:
                m.utils.END_OF_TERM.main()
            except:
                print("-" * 25)
                traceback.print_exc()
        print("=" * 50)
    print("=" * 50)
    print("=" * 50)


############################################################################

if __name__ == "__main__":
    main()

############################################################################
#
