from __future__ import print_function, unicode_literals

#######################
#######################
import shouts

from .context_processors import get_important_dates_queryset

##
## NOTE:
##  * You cannot use reverse() url matching here, since autodiscover()
##      is typically called in the url conf, and thus patterns may not
##      be loaded yet. [UNLESS shouts.autodiscover() is **last**.]
##

shouts.sources.register(
    "Important Date",
    get_important_dates_queryset,
    # verbose_name=..., # default
    template_name="classes/shouts/impdate_%s.html",
)
