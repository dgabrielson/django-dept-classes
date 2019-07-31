"""
Views for the classes api.
"""
#######################
from __future__ import print_function, unicode_literals

import datetime
import json

from django import http
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.db.models.query import QuerySet
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from ..models import ImportantDate

#######################
#################################################################

#################################################################
#################################################################
##### JSON API goodness
#################################################################
#################################################################


class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return http.HttpResponse(
            content, content_type="application/json", **httpresponse_kwargs
        )

    def json_safe_value(self, value):
        if isinstance(value, datetime.date):
            return "{}".format(value)
        if isinstance(value, datetime.time):
            return "{}".format(value)
        if isinstance(value, datetime.datetime):
            return "{}".format(value)
        return value

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)


#################################################################

#################################################################


class JSONDetailView(JSONResponseMixin, BaseDetailView):
    """
    Process the object. (It most be a model instance.)
    The object is required to have the as_dict() method.
    """

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        object = context["object"]
        if not isinstance(object, Model):
            raise ImproperlyConfigured(
                "API detail calls can only work on models (got type %s)"
                % type(object_list)
            )
        fields = [f.name for f in object._meta.fields]
        values = [self.json_safe_value(getattr(object, f)) for f in fields]
        data = dict(zip(fields, values))
        return json.dumps(data)


#################################################################


class JSONListView(JSONResponseMixin, BaseListView):
    """
    Process the object_list. (It must be a queryset.)
    """

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        object_list = context["object_list"]
        if not isinstance(object_list, QuerySet):
            raise ImproperlyConfigured(
                "API list calls can only work on querysets (got type %s)"
                % type(object_list)
            )
        fields = [f.name for f in object_list.model._meta.fields]
        values_list = object_list.values_list(*fields)
        data = [
            dict(zip(fields, [self.json_safe_value(v) for v in values]))
            for values in values_list
        ]
        return json.dumps(data)


#################################################################
#################################################################
##### Class API mixins
#################################################################
#################################################################


class ImportantDateMixin(object):
    """
    Basic Important Date mixin
    """

    queryset = ImportantDate.objects.active()


#################################################################


class ImportantDateFutureMixin(object):
    """
    Only future Important Dates mixin
    """

    queryset = ImportantDate.objects.after(datetime.date.today())


#################################################################
#################################################################
##### API Views
#################################################################
#################################################################


class ImportantDatesAllListView(ImportantDateMixin, JSONListView):
    pass


important_dates_all = ImportantDatesAllListView.as_view()


class ImportantDatesFutureListView(ImportantDateFutureMixin, JSONListView):
    pass


important_dates_future = ImportantDatesFutureListView.as_view()


class ImportantDateDetailView(ImportantDateMixin, JSONDetailView):
    pass


important_dates_detail = ImportantDateDetailView.as_view()

#################################################################
#################################################################
#################################################################
