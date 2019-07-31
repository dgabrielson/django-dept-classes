"""
Haystack search indexes for Classes application.
"""
#######################
from __future__ import print_function, unicode_literals

from haystack import indexes

from .models import Course

#######################
###############################################################

###############################################################


class CourseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr="modified")

    def get_model(self):
        return Course

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.advertised()


###############################################################
