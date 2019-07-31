"""
Managers for the classes application.
"""
#######################
from __future__ import print_function, unicode_literals

import datetime

from django.db import models

from .choices import TERMS
from .querysets import (
    CourseHandoutQuerySet,
    CourseQuerySet,
    DepartmentQuerySet,
    ImportantDateQuerySet,
    SectionHandoutQuerySet,
    SectionQuerySet,
    SectionScheduleQuerySet,
    SemesterQuerySet,
)

#######################
#######################################################################

#######################################################################
#######################################################################
#######################################################################


class CustomQuerySetManager(models.Manager):
    """
    Custom Manager for an arbitrary model, just a wrapper for returning
    a custom QuerySet
    """

    queryset_class = models.query.QuerySet
    always_select_related = None

    def get_queryset(self):
        """
        Return the custom QuerySet
        """
        queryset = self.queryset_class(self.model)
        if self.always_select_related is not None:
            queryset = queryset.select_related(*self.always_select_related)
        return queryset


#######################################################################
#######################################################################
#######################################################################


class TimeslotManager(CustomQuerySetManager):
    def TBA(self):
        """
        Returns the 'TBA' timeslot.
        Creates this in the database if it does not exist.
        """
        timeslot, flag = self.get_or_create(
            name="None",
            day="n/a",
            start_time=datetime.time(0, 0, 0),
            stop_time=datetime.time(11, 59, 59),
        )
        return timeslot

    def Online(self):
        """
        Returns the 'Online' timeslot.
        Creates this in the database if it does not exist.
        """
        timeslot, flag = self.get_or_create(
            name="Online",
            day="-",
            start_time=datetime.time(0, 0, 0),
            stop_time=datetime.time(23, 59, 59),
            scheduled=True,
        )
        return timeslot


#######################################################################


class CourseManager(CustomQuerySetManager):
    """
    Manager for Course objects.
    """

    queryset_class = CourseQuerySet
    always_select_related = ["department"]

    def get_current(self, **filters):
        """
        Return a queryset for the current courses.
        """
        from .models import Section

        section_list = Section.objects.get_current()
        pk_list = section_list.values_list("course", flat=True)
        return self.filter(pk__in=pk_list, **filters)

    def get_next_term(self, **filters):
        """
        Return a queryset for next term's outlines.
        """
        from .models import Section

        section_list = Section.objects.get_next_term()
        pk_list = section_list.values_list("course", flat=True)
        return self.filter(pk__in=pk_list, **filters)

    def get_current_and_next_term(self, **filters):
        """
        Return a list of term, course_list pairs.
        """
        from .models import Semester

        current_term = Semester.objects.get_current()
        next_term = current_term.get_next()
        return [
            (current_term, self.get_current(**filters)),
            (next_term, self.get_next_term(**filters)),
        ]

    def get_by_slug(self, slug):
        """
        undo  minimal slugging for a short name.

        NOTE/TODO:
        This is not robust with the new Department-code / Course-code
        implementation.  It should be removed from url pattern usage.
        """
        name = slug.replace("-", " ")  # simple unslugging.
        try:
            dept_code, course_code = name.split(None, 1)
        except ValueError:
            raise self.model.DoesNotExist
        return self.get(
            active=True, department__code__iexact=dept_code, code__iexact=course_code
        )

    def get_upcoming(self, **filter):
        """
        Similar to advertise, below; however fetches more courses for any
        of the current and future terms.
        """
        from .models import Section

        sections = Section.objects.get_current_or_future()
        pk_set = set(sections.values_list("course", flat=True))
        return self.filter(active=True, pk__in=pk_set)

    def upcoming_grad(self, **filter):
        """
        This might be a bit of a UofM specific hack... exclude
        1000 and 2000 level courses.
        """
        upcoming = self.get_upcoming()
        upcoming = upcoming.exclude(code__startswith="1")
        upcoming = upcoming.exclude(code__startswith="2")
        return upcoming

    def advertised(self, **filters):
        """
        Get a queryset mapping to advertised courses.
        """
        qs = self.filter(active=True)
        if filters:
            qs = qs.filter(**filters)
        qs = qs.filter(department__advertised=True)
        return qs


CourseManager = CourseManager.from_queryset(CourseQuerySet)

#######################################################################


class SemesterManager(CustomQuerySetManager):
    """
    Provide extra methods for Semester objects.
    """

    queryset_class = SemesterQuerySet

    def __start_date(self, year, term):
        if term == "1":
            return datetime.date(year, 1, 1)
        if term[0] == "2":
            return datetime.date(year, 5, 1)
        if self.term == "3":
            return datetime.date(year, 9, 1)

    def term_code_to_name(self, term_code):
        for k, v in TERMS:
            if k == term_code:
                return v

    def term_name_to_code(self, term_name):
        for k, v in TERMS:
            if v.lower() == term_name.lower():
                return k

    def get_current_raw_tuple(self):
        """
        Return the current semester as a year, term tuple.
        """
        today = datetime.date.today()
        if 1 <= today.month <= 4:
            term = "1"
        if 5 <= today.month <= 8:
            term = "2"
        if 9 <= today.month <= 12:
            term = "3"
        return today.year, term

    def get_current_year_name(self):
        year, term = self.get_current_raw_tuple()
        return year, self.term_code_to_name(term)

    def get_current_display(self):
        year, name = self.get_current_year_name()
        return "%s %d" % (name, year)

    def get_next_raw_tuple(self):
        """
        Return the next semester as a year, term tuple
        """
        year, term = self.get_current_raw_tuple()
        i_term = int(term)
        i_term += 1
        if i_term == 4:
            i_term = 1
            year += 1
        return year, str(i_term)

    def get_next_year_name(self):
        year, term = self.get_next_raw_tuple()
        return year, self.term_code_to_name(term)

    def get_next_display(self):
        year, name = self.get_next_year_name()
        return "%s %d" % (name, year)

    def get_current_qs(self):
        """
        Return the current semester as a query set.
        This is always a query set to allow for Summer session.
        """
        year, term = self.get_current_raw_tuple()
        return self.filter(year=year, term__startswith=term)

    def get_current(self):
        """
        Return the current semester.
        This returns the generic 'Summer' session Semester in summer.
        """
        return self.get_by_date(datetime.date.today())

    def current_percent(self):
        """
        returns the amount of the way through the current term, as a
        true percentage (float in the interval 0, 1)
        """
        curr = self.get_current()
        today = datetime.date.today()
        start, finish = curr.get_start_finish_dates()
        d1 = today - start
        d2 = finish - start
        f1 = float(d1.days)
        f2 = float(d2.days)
        return f1 / f2

    def get_current_or_future(self):
        """
        returns all current or future Semester objects in the database.

        Does *not* create new objects.
        """
        qs = self.filter(active=True)
        year, term = self.get_current_raw_tuple()

        future_years = models.Q(year__gt=year)

        if term == "1":
            this_year = models.Q(year=year)
        elif term == "2":
            this_year = models.Q(year=year, term__startswith="2") | models.Q(
                year=year, term="3"
            )
        elif term == "3":
            this_year = models.Q(year=year, term="3")
        else:
            assert (
                False
            ), "unknown term code from SemesterManager.get_current_raw_tuple()"

        qs = qs.filter(this_year | future_years)
        return qs

    def get_next_qs(self):
        """
        Returns the next Semester object(s) in the database.

        Does *not* create new objects.
        """
        year, term = self.get_next_raw_tuple()
        return self.filter(year=year, term__startswith=term)

    def get_current_or_next_qs(self):
        """
        Returns semester objects corresponding to this term, or next term.
        """
        curr_year, curr_term = self.get_current_raw_tuple()
        next_year, next_term = self.get_next_raw_tuple()

        current_Q = models.Q(year=curr_year, term__startswith=curr_term)
        next_Q = models.Q(year=next_year, term__startswith=next_term)
        return self.filter(current_Q | next_Q)

    def get_by_date(self, date):
        """
        Returns a semester object corresponding to the given date.
        This object is created if it doesn't yet exist.
        """
        term = str((date.month - 1) // 4 + 1)
        year = date.year
        object, created_flag = self.get_or_create(year=year, term=term)
        return object

    def filter_by_date_range(self, start, end):
        if not start < end:
            raise ValueError("start must be less than end")
        start_term = str((start.month - 1) // 4 + 1)
        end_term = str((end.month - 1) // 4 + 1)
        if start.year == end.year:
            return self.filter(
                year=start.year, term__gte=start_term, term__lte=end_term
            )
        else:
            start_year_Q = models.Q(year=start.year, term__gte=start_term)
            end_year_Q = models.Q(year=end.year, term__lte=end_term)
            middle_years_Q = models.Q(year__gt=start.year, year__lt=end.year)
            return self.filter(start_year_Q | middle_years_Q | end_year_Q)

    def get_by_pair(self, year, term_name):
        """
        Returns a semester object corresponding to the given pair.
        """
        try:
            year = int(year)  # make sure
        except ValueError:
            raise ValueError("year not convertable to an integer" % term_name)

        term = self.term_name_to_code(term_name)
        if not term:
            raise ValueError("Could not find an associated term for %r" % term_name)

        object, created_flag = self.get_or_create(year=year, term=term)
        return object

    def get_by_name(self, name):
        """
        Returns a semester object corresponding to the given name.
        It is expected to be in the format "term NNNN".
        """
        term_name, year = name.split()
        return self.get_by_pair(year, term_name)


SemesterManager = SemesterManager.from_queryset(SemesterQuerySet)

#######################################################################


class SemesterDateRangeManager(CustomQuerySetManager):
    def find(self, start, finish):
        """
        Gets or creates (and returns) a new SemesterDateRange object.
        Automatically determines and sets the semester.
        """

        try:
            return self.get(start=start, finish=finish)
        except self.model.DoesNotExist:
            from .models import Semester

            semester = Semester.objects.get_by_date(finish)
            date_range = self.create(semester=semester, start=start, finish=finish)
            return date_range


#######################################################################


class SectionManager(CustomQuerySetManager):
    """
    Custom Manager for Section objects.
    """

    queryset_class = SectionQuerySet
    always_select_related = ["course", "course__department", "instructor"]

    #################################
    # Historic manager methods:
    #################################

    def get_current(self, **filters):
        """
        Return a queryset for the current classes.
        """
        from .models import Semester

        qs = self.filter(
            active=True, course__active=True, term__in=Semester.objects.get_current_qs()
        )
        return qs.filter(**filters)

    def get_next_term(self, **filters):
        """
        Return a queryset for next term's classes.
        """
        from .models import Semester

        qs = self.filter(course__active=True, term__in=Semester.objects.get_next_qs())
        return qs.filter(**filters)

    def get_current_or_future(self, **filters):
        from .models import Semester

        qs = self.filter(
            course__active=True, term__in=Semester.objects.get_current_or_future()
        )
        return qs.filter(**filters)

    def find(self, *args, **kwargs):
        """
        Provide a smoother interface to ``get``.

        ``args`` could be, e.g.,
            ``3750``, ``"STAT 2400"``, ``"STAT 1000 A03"``
            (only the last one is used).

        ``kwargs`` can be any of:
            ``term=obj``, ``course="STAT 1000"``, ``section="A03"``,
            ``instructor="Zenadia Mateo"``

        ``kwargs`` will override ``args``, as appropriate.
        """
        terms = {}

        if len(args) > 1:
            raise ValueError("Cannot find more than one section")

        if args:
            arg = args[0]
            elements = arg.split()
            if len(elements) not in [2, 3]:
                raise ValueError(
                    'non-keyword argument must be either "STAT 2400" or "STAT 1000 A01"'
                )
            kwargs["department"] = elements[0]
            kwargs["course"] = elements[1]
            if len(elements) >= 3:
                kwargs["section"] = elements[2]

        if "term" not in kwargs:
            from .models import Semester

            terms["active"] = True
            terms["term__in"] = Semester.objects.get_current_qs()
        else:
            terms["term"] = kwargs["term"]

        if "department" in kwargs:
            terms["course__department__code__iexact"] = kwargs["department"]

        if "course" in kwargs:
            terms["course__code__iexact"] = kwargs["course"]

        if "section" in kwargs:
            terms["section_name__iexact"] = kwargs["section"]

        if "instructor" in kwargs:
            terms["instructor__cn__iexact"] = kwargs["instructor"]

        return self.get(**terms)


SectionManager = SectionManager.from_queryset(SectionQuerySet)

#######################################################################


class SectionScheduleManager(CustomQuerySetManager):
    """
    Custom Manager for PageFiles, just a wrapper for returning the
    custom QuerySet
    """

    queryset_class = SectionScheduleQuerySet


SectionScheduleManager = SectionScheduleManager.from_queryset(SectionScheduleQuerySet)

#######################################################################


class CourseHandoutManager(CustomQuerySetManager):
    always_select_related = ["course", "course__department"]
    queryset_class = CourseHandoutQuerySet


CourseHandoutManager = CourseHandoutManager.from_queryset(CourseHandoutQuerySet)

#######################################################################


class SectionHandoutManager(CustomQuerySetManager):
    always_select_related = [
        "section",
        "section__term",
        "section__course",
        "section__course__department",
    ]
    queryset_class = SectionHandoutQuerySet


SectionHandoutManager = SectionHandoutManager.from_queryset(SectionHandoutQuerySet)

#######################################################################


class ImportantDateManager(CustomQuerySetManager):
    """
    Manager class for important dates.  Proxy to ImportantDateQuerySet.
    """

    queryset_class = ImportantDateQuerySet


ImportantDateManager = ImportantDateManager.from_queryset(ImportantDateQuerySet)

#######################################################################


class DepartmentManager(CustomQuerySetManager):
    """
    Manager class for Department objects.
    Proxy to DepartmentQuerySet.
    """

    queryset_class = DepartmentQuerySet


DepartmentManager = DepartmentManager.from_queryset(DepartmentQuerySet)

#######################################################################
