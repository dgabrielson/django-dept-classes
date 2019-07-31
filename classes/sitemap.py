"""
Sitemap for classes app.
"""
#######################
from __future__ import print_function, unicode_literals

#######################
from django.contrib.sitemaps import GenericSitemap

from .models import Course

Course_Sitemap = GenericSitemap({"queryset": Course.objects.advertised()})
