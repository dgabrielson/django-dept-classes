#######################
from __future__ import print_function, unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

#######################
#########################################################################

#########################################################################


class ClassesConfig(AppConfig):
    name = "classes"
    verbose_name = _("Classes")

    def ready(self):
        """
        Any app specific startup code, e.g., register signals,
        should go here.
        """


#########################################################################
