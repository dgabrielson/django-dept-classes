#######################
from __future__ import print_function, unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

#######################
#########################################################################

#########################################################################


class AuroraConfig(AppConfig):
    name = "aurora"
    verbose_name = _("Banner Integration")

    def ready(self):
        """
        Any app specific startup code, e.g., register signals,
        should go here.
        """


#########################################################################
