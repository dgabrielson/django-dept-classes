"""
Custom querysets for the classes application.
"""
#######################
from __future__ import print_function, unicode_literals

import datetime

from django.core.exceptions import ImproperlyConfigured
from django.db import models

#######################
#######################################################################

#######################################################################
#######################################################################


class BaseCustomQuerySet(models.query.QuerySet):
    """
    Custom QuerySet.
    """

    def active(self):
        """
        Returns only the active items in this queryset
        """
        return self.filter(active=True)


#######################################################################
#######################################################################


class DepartmentQuerySet(BaseCustomQuerySet):
    """
    Custom query set for Department objects.
    """

    def advertised(self):
        return self.filter(advertised=True)

    def public(self):
        return self.filter(public=True)


#     def get_default(self):
#         return self.get(code=conf.get('default_class_code'))

#######################################################################


class CourseQuerySet(BaseCustomQuerySet):
    """
    Custom query set for Course objects.
    """


#######################################################################


class SectionQuerySet(BaseCustomQuerySet):
    """
    Custom query set for this model.
    """

    def active(self):
        """
        Returns only items with the active flag.
        """
        return self.filter(active=True).select_related()

    def sectionschedule_list(self):
        """
        For the current queryset, get the list of corresponding
        section schedules.
        """
        raise RuntimeError("Use sectionschedule_set instead of sectionschedule_list")
        from .models import SectionSchedule

        pk_list = self.values_list("pk", flat=True)
        return SectionSchedule.objects.filter(section__pk__in=pk_list)

    def get_start_finish_dates(self):
        """
        Return the limits of the SectionSchedule object attached
        to this queryset
        """
        return self.sectionschedule_set.active().date_range()

    def current(self, reference_date=None, grace=0):
        """
        Filters the queryset so that only sections with a section schedule
        containing the given reference_date are returned.
        If reference_date is None, then today is used.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        A = reference_date
        B = A - datetime.timedelta(days=grace)
        return self.filter(
            sectionschedule__date_range__start__lte=A,
            sectionschedule__date_range__finish__gte=B,
        ).distinct()

    def current_or_future(self, reference_date=None):
        """
        Filters the queryset so that only sections with a section schedule
        containing the given reference_date are returned.
        If reference_date is None, then today is used.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        return self.filter(
            sectionschedule__date_range__start__gte=reference_date
        ).distinct()

    def historical(self, reference_date=None):
        """
        Filters the queryset so that only sections with a section schedule
        ending before the given reference_date are returned.
        If reference_date is None, then today is used.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        return self.filter(
            sectionschedule__date_range__start__lt=reference_date
        ).distinct()

    def advertised(self):
        """
        Filters the current query set for advertised course sections only.
        """
        return self.filter(course__department__advertised=True)

    def for_course(self, course):
        """
        Filters the section objects for the given course.
        """
        return self.filter(course=course)

    def by_instructor(self, person=None, user=None, username=None):
        """
        Restrict QuerySet by instructor.  One of ``person``, ``user``,
        or ``username`` must be supplied.
        """
        if person is not None:
            return self.filter(instructor=person)
        if user is not None:
            username = user.username
        if username is not None:
            return self.filter(instructor__username=username)
        raise ImproperlyConfigured(
            "{0!r}.by_instructor() must supply one of 'person', 'user', or 'username' keyword arguments".format(
                self.__class__.__name__
            )
        )

    def active_terms(self):
        return self.filter(term__active=True)

    def advertised_terms(self):
        qs = self.filter(term__active=True, term__advertised=True)
        qs = qs.select_related("instructor")
        return qs

    def current_term(self):
        term = Semester.objects.get_current()
        return self.filter(term=term)

    def sectionhandout_qs(self, active=True):
        from .models import SectionHandout

        id_list = self.values_list("sectionhandout__id", flat=True)
        qs = SectionHandout.objects.filter(id__in=id_list)
        if active:
            qs = qs.filter(active=True)
        return qs


#######################################################################


class SectionScheduleQuerySet(BaseCustomQuerySet):
    """
    Custom query set for this model.
    """

    def active(self):
        """
        Returns only items with the active flag.
        """
        return self.filter(active=True).select_related(
            "date_range", "timeslot", "room", "section", "type", "instructor"
        )

    def section_list(self):
        """
        For the current queryset, return a queryset of the corresponding
        sections.
        """
        from .models import Section

        pk_list = self.values_list("section", flat=True).distinct()
        return Section.objects.filter(pk__in=pk_list)

    def current_or_future(self, reference_date=None):
        """
        Filter out section schedules that have a semester date range with
        a finish date in the past (before dtcurrent).
        If reference_date is not given, it defaults to today.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        return self.filter(date_range__isnull=False).exclude(
            date_range__finish__lte=reference_date
        )

    def current(self, reference_date=None, grace=0):
        """
        Only schedules bracketing the given reference date.
        If reference_date is not given, it defaults to today.
        If ``grace`` is given, then this many days past the end of the
        reference date is still "current"
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        qs = self.current_or_future(reference_date=reference_date)
        finish = reference_date + datetime.timedelta(days=grace)
        return qs.exclude(date_range__start__gte=finish)

    def active_terms(self):
        return self.filter(section__term__active=True)

    def current_term(self):
        from .models import Semester

        term = Semester.objects.get_current()
        return self.filter(section__term=term)

    def instructor(self):
        """
        If there is only one instructor for any of the items in the
        current queryset (or one + None); return them, otherwise
        return None
        """
        instructor_list = (
            self.filter(instructor__isnull=False)
            .order_by("instructor")
            .values_list("instructor", flat=True)
            .distinct()
        )
        if len(instructor_list) == 1:
            from people.models import Person

            return Person.objects.get(pk=instructor_list[0])

    def additional_instructors(self):
        """
        Like above, but substantially more expensive.
        Returns an set of people (or an empty set).
        """
        addl = set()
        for o in self.iterator():
            opl = set([p for p in o.additional_instructors.all()])
            if opl:
                if not addl:
                    addl = opl
                elif addl != opl:
                    return set()
        return addl

    def room(self):
        """
        If there is only one room for any of the items in the
        current queryset (or one + None); return them, otherwise
        return None
        """
        room_list = set(self.filter(room__isnull=False).values_list("room", flat=True))
        if len(room_list) == 1:
            from places.models import ClassRoom

            return ClassRoom.objects.get(pk=room_list.pop())

    def timeslot(self):
        """
        If there is only one timeslot for any of the items in the
        current queryset return it, otherwise return None
        """
        timeslot_list = set(self.values_list("timeslot", flat=True))
        if len(timeslot_list) == 1:
            from classes.models import Timeslot

            return Timeslot.objects.get(pk=timeslot_list.pop())

    def date_range(self):
        """
        Return the first and last dates indicated by the current date range.
        """
        results = self.aggregate(
            min=models.Min("date_range__start"), max=models.Max("date_range__finish")
        )
        start = results["min"]
        finish = results["max"]
        return start, finish


#######################################################################


class ImportantDateQuerySet(BaseCustomQuerySet):
    """
    Custom QuerySet for ImportantDate objects.
    """

    def in_date_range(self, start, end):
        """
        Restricts the QuerySet to active items in the given
        date range (inclusive).
        """
        date_range = (start, end)
        query = models.Q(date__range=date_range) | models.Q(end_date__range=date_range)
        return self.active().filter(query).distinct()

    def before(self, d):
        """
        Restricts the QuerySet to active items before the given
        date (inclusive).
        """
        query = models.Q(date__lte=d) | models.Q(end_date__lte=d)
        return self.active().filter(query).distinct()

    def after(self, d):
        """
        Restricts the QuerySet to active items after the given
        date (inclusive).
        """
        return self.active().filter(date__gte=d)


#######################################################################


class SemesterQuerySet(BaseCustomQuerySet):
    """
    Custom QuerySet for Semester objects.
    """

    def advertised(self):
        return self.filter(active=True, advertised=True)


#######################################################################


class CourseHandoutQuerySet(BaseCustomQuerySet):
    """
    Custom QuerySet for CourseHandout objects.
    """

    def public(self):
        """
        Implies active as well.
        """
        return self.filter(active=True, public=True)


#######################################################################


class SectionHandoutQuerySet(BaseCustomQuerySet):
    """
    Custom QuerySet for SectionHandout objects.
    """


#######################################################################


class RequisiteQuerySet(BaseCustomQuerySet):
    """
    Custom QuerySet for Requisite objects.
    """

    def ranked(self):
        qs = self.active()
        qs = qs.filter(rank__isnull=False)
        qs = qs.filter(course__active=True, course__department__active=True)
        qs = qs.order_by("rank")
        return qs


#######################################################################


class PrerequisiteQuerySet(BaseCustomQuerySet):
    """
    Custom QuerySet for Prerequisite objects.
    """

    def active(self):
        qs = super().active()
        qs = qs.filter(requisite__active=True)
        return qs


#######################################################################
#######################################################################
