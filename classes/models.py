"""
Classes Models
"""
# -*- coding: utf-8 -*-
#######################
from __future__ import print_function, unicode_literals

import datetime

import dateutil.relativedelta
import vobject
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.template.defaultfilters import title
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.text import capfirst, slugify
from django.utils.timezone import get_current_timezone, localtime, make_aware, now, utc
from webcal import formatters as calfmt
from webcal.utils import make_icalendar

from . import conf, utils
from .choices import TERMS
from .managers import (
    CourseHandoutManager,
    CourseManager,
    DepartmentManager,
    ImportantDateManager,
    SectionHandoutManager,
    SectionManager,
    SectionScheduleManager,
    SemesterDateRangeManager,
    SemesterManager,
    TimeslotManager,
)
from .querysets import PrerequisiteQuerySet, RequisiteQuerySet

#################################################################
#################################################################
#################################################################


class ClassesBaseModel(models.Model):
    """
    An abstract base class.
    """

    active = models.BooleanField(
        default=True,
        help_text="Uncheck this to remove this item " + "without actually deleting it.",
    )
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="creation time"
    )
    modified = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="last modification time"
    )

    class Meta:
        abstract = True


#################################################################
#################################################################
#################################################################


@python_2_unicode_compatible
class Department(ClassesBaseModel):
    """
    A department is a unit that contains courses.
    """

    code = models.CharField(
        max_length=16,
        help_text="A short character sequence which is used to construct course names, e.g., BIOL or GRAD",
    )
    name = models.CharField(
        max_length=64,
        help_text="Verbose name of the department, e.g., 'Biology' or 'Graduate Studies'",
    )
    slug = models.SlugField(
        unique=True, help_text="A url which identifies the department"
    )
    description = models.TextField(blank=True)

    advertised = models.BooleanField(
        default=True,
        help_text="A department should be advertised if you are authoritive for it",
    )
    public = models.BooleanField(
        default=True,
        help_text="If a department is public, then it's course pages are available",
    )

    objects = DepartmentManager()

    class Meta:
        ordering = ["code"]
        base_manager_name = "objects"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("classes-department-detail", kwargs={"slug": self.slug})


#################################################################


@python_2_unicode_compatible
class Timeslot(ClassesBaseModel):
    """
    A timeslot is when a class occurs at the UofM.
    """

    name = models.CharField(max_length=64)
    day = models.CharField(
        max_length=16,
        help_text='This should be a substring of "MTWRF".',
        validators=[RegexValidator(regex="M?T?W?R?F?S?")],
    )
    start_time = models.TimeField()
    stop_time = models.TimeField()
    scheduled = models.BooleanField(default=False, verbose_name="Use for scheduling")

    objects = TimeslotManager()

    class Meta:
        ordering = ["day", "start_time", "stop_time"]
        unique_together = ("day", "start_time", "stop_time")
        base_manager_name = "objects"

    def __str__(self):
        return self.name

    def label(self):
        if self.name.startswith("Lab "):
            return "Lab"
        if self.name.startswith("Time "):
            return "Time"
        return self.name

    def get_day_display(self):
        result = []
        if "M" in self.day:
            result.append("M")
        if "T" in self.day:
            result.append("Tu")
        if "W" in self.day:
            result.append("W")
        if "R" in self.day:
            result.append("Th")
        if "F" in self.day:
            result.append("F")
        if "S" in self.day:  # sometimes things hit Saturday
            result.append("S")
        if result:
            return ".".join(result) + "."
        return ""

    def get_start_time_display(self):
        if self.name in ["None", "Online"]:
            return ""
        s = self.start_time.strftime(conf.get("timeslot:display:time_format"))
        if conf.get("timeslot:display:trim_leading_zeros"):
            s = s.lstrip("0")
        return s

    def get_stop_time_display(self):
        if self.name in ["None", "Online"]:
            return ""
        s = self.stop_time.strftime(conf.get("timeslot:display:time_format"))
        if conf.get("timeslot:display:trim_leading_zeros"):
            s = s.lstrip("0")
        return s

    def get_time_display(self):
        if self.name in ["None", "Online"]:
            return ""
        return self.get_start_time_display() + "\u2013" + self.get_stop_time_display()

    def get_time_display_ascii(self):
        """
        This function is here so that e.g., export CSV
        files works properly.
        """
        if self.name in ["None", "Online"]:
            return ""
        return self.get_start_time_display() + " - " + self.get_stop_time_display()

    def display(self):
        if self.name == "Online":
            return self.name
        if self.name == "None":
            return ""
        day_str = self.get_day_display()
        return self.get_time_display() + ", " + day_str

    def get_rrule_days(self):
        result = []
        if "M" in self.day:
            result.append(dateutil.rrule.MO)
        if "T" in self.day:
            result.append(dateutil.rrule.TU)
        if "W" in self.day:
            result.append(dateutil.rrule.WE)
        if "R" in self.day:
            result.append(dateutil.rrule.TH)
        if "F" in self.day:
            result.append(dateutil.rrule.FR)
        if "S" in self.day:
            result.append(dateutil.rrule.SA)
        return result


#################################################################


@python_2_unicode_compatible
class Course(ClassesBaseModel):
    """
    An individual course.  Belongs to a specific department, may
    be cross listed.  Does not refer to an actual Section.
    """

    department = models.ForeignKey(
        Department,
        null=True,
        on_delete=models.PROTECT,
        limit_choices_to={"active": True},
    )
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=150)
    slug = models.SlugField(
        unique=True, help_text="A url fragment which identies this course"
    )
    description = models.TextField(blank=True)
    detailed_program = models.TextField(blank=True)

    # prerequisites? co-requisites? not-to-be-held-withs?
    objects = CourseManager()

    class Meta:
        ordering = ["department", "code"]
        base_manager_name = "objects"

    def __str__(self):
        if not self.department:
            s = self.code
        else:
            s = self.department.code + " " + self.code
        return s + " - " + self.name

    def get_absolute_url(self):
        return reverse("classes-course-detail", kwargs={"slug": self.slug})

    @property
    def label(self):
        return self.department.code + " " + self.code

    @property
    def label_nbsp(self):
        """
        Use unicode non-breaking space -- these should never
        be split.
        """
        return self.department.code + "\u00a0" + self.code

    @property
    def reverse_prerequisites(self):
        """
        Return a queryset that this course is a prerequsite for.
        """

        def _get_prereq(c):
            try:
                return c.prerequisite_set.active().get(requisite__course_id=self.pk)
            except (Prerequisite.DoesNotExist, Prerequisite.MultipleObjectsReturned):
                return None

        course_qs = Course.objects.filter(
            active=True,
            department__active=True,
            prerequisite__active=True,
            prerequisite__requisite__active=True,
            prerequisite__requisite__course_id=self.pk,
        )
        return [(c, _get_prereq(c)) for c in course_qs]

    @property
    def map_svg_data(self):
        from .views import course_graphviz_svg_data

        data = course_graphviz_svg_data(self)
        return mark_safe(data.decode("utf-8"))


#################################################################


@python_2_unicode_compatible
class Requisite(ClassesBaseModel):
    course = models.ForeignKey(
        Course,
        null=True,
        blank=True,
        help_text="A local course",
        on_delete=models.CASCADE,
    )
    outside_course = models.CharField(
        max_length=128, blank=True, help_text="A description for an external requisite"
    )
    url = models.URLField(blank=True, help_text="A link to the requisite (optional)")
    note = models.CharField(
        max_length=128,
        blank=True,
        help_text="Additional information for this requisite",
    )
    rank = models.SmallIntegerField(
        default=None,
        null=True,
        blank=True,
        help_text="Same rank items will be logically grouped where appropriate",
    )

    objects = RequisiteQuerySet.as_manager()

    class Meta:
        base_manager_name = "objects"
        ordering = ("outside_course", "course")
        unique_together = (("course", "outside_course"),)

    def __str__(self):
        if self.outside_course:
            return self.outside_course
        if self.course is not None:
            return self.course.label
        return "???"

    def clean(self, *args, **kwargs):
        s = super().clean(*args, **kwargs)
        if self.course is None and not self.outside_course:
            raise ValidationError(
                "Either a course or an outside course description is required"
            )
        if self.course is not None and self.outside_course:
            raise ValidationError("Only one of course or outside course is allowed")
        return s

    def get_absolute_url(self):
        if self.url:
            return self.url
        if self.course:
            return self.course.get_absolute_url()
        return None

    def get_note(self):
        if self.note:
            return self.note
        if self.course:
            return self.course.name
        return None


#################################################################


@python_2_unicode_compatible
class Prerequisite(ClassesBaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    requisite = models.ForeignKey(Requisite, on_delete=models.CASCADE)
    equiv_group = models.SmallIntegerField(default=1)
    minimum_grade = models.CharField(max_length=64, blank=True)
    preferred = models.BooleanField()
    corequisite = models.BooleanField()
    optional = models.BooleanField()

    objects = PrerequisiteQuerySet.as_manager()

    class Meta:
        base_manager_name = "objects"
        ordering = ("equiv_group", "-preferred", "requisite")

    def __str__(self):
        return str(self.requisite)

    def get_absolute_url(self):
        return self.requisite.get_absolute_url()


#################################################################


@python_2_unicode_compatible
class Semester(ClassesBaseModel):
    """
    Manager methods:
        Semester.objects.get_current_raw_tuple() -> year, term_code
        Semester.objects.get_current() -> <Semester object>

    methods:
        semester.is_current() -> <boolean>
        semester.sort_key() : use for list sorting
    """

    year = models.SmallIntegerField(default=datetime.date.today().year)
    term = models.CharField(max_length=2, choices=TERMS)
    slug = models.SlugField(
        unique=True, help_text="A url fragment which identifies this semester"
    )
    advertised = models.BooleanField(
        default=False,
        help_text="A semester should be advertised if relevant information should be displayed.",
    )

    objects = SemesterManager()

    class Meta:
        ordering = ["year", "term"]
        base_manager_name = "objects"

    def __str__(self):
        return "{} {}".format(self.get_term_display(), self.year)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify("{}".format(self))
        return super(Semester, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("classes-semester-detail", kwargs={"slug": self.slug})

    def sort_key(self):
        return "{}.{}".format(self.year, self.term)

    def is_current(self):
        year, term = Semester.objects.get_current_raw_tuple()
        return self.year == year and self.term[0] == term

    def is_current_tag(self):
        """
        Like is_current, but returns an admin suitable tag.
        """
        from django.contrib.admin.templatetags.admin_list import _boolean_icon

        return _boolean_icon(self.is_current())

    is_current_tag.short_description = "Current"
    is_current_tag.allow_tags = True

    def is_current_or_future(self):
        year, term = Semester.objects.get_current_raw_tuple()
        if self.year > year:
            return True
        return self.year == year and self.term[0] >= term

    def get_start_finish_dates(self):
        """
        Retrieves the earliest start and the latest finish from all
        associated SemesterDateRange's.

        This is robust: if there are no SemesterDateRange's
        associated with this instance, than the return value will still
        be (relatively) meaningful based on the term,
        i.e., Jan - Apr; May - Aug; Sep - Dec.
        """
        results = self.semesterdaterange_set.aggregate(
            min=models.Min("start"), max=models.Max("finish")
        )
        start = results["min"]
        finish = results["max"]

        term_int = int(self.term[0])
        if start is None:
            month = 4 * (term_int - 1) + 1
            start = datetime.date(self.year, month, 1)
        if finish is None:
            month = 4 * term_int + 1
            year = self.year
            if month > 12:
                month -= 12
                year += 1
            finish = datetime.date(year, month, 1) - datetime.timedelta(days=1)

        return start, finish

    def get_next(self, n=1):
        """
        This returns the next n'th term from the database.
        If the requested term does not exist, it is automatically created.
        """
        term = int(self.term[0]) + n
        year = self.year
        load_new_dates = False
        while term > 3:
            term -= 3
            year += 1
            load_new_dates = True

        termcode = "{}".format(term)
        termlabel = dict(TERMS).get(termcode, termcode)
        slug = slugify("{} {}".format(termlabel, year))
        defaults = {"slug": slug, "active": True}
        semester, created_flag = Semester.objects.get_or_create(
            year=year, term="{}".format(term), defaults=defaults
        )
        if created_flag and load_new_dates:
            utils.load_dates(year)
        return semester

    @property
    def course_list(self):
        """
        Returns a queryset of *courses* offered in this term (not sections)
        """
        pk_set = set(self.section_set.values_list("course_id", flat=True))
        return Course.objects.advertised(pk__in=pk_set)


@python_2_unicode_compatible
class SemesterDateRange(ClassesBaseModel):
    """
    This class defines a date range for classes in a term.
    There can be several of these -- that's okay, but this way
    there is only one Semester object, not multiples.
    """

    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        limit_choices_to={"active": True, "advertised": True},
    )
    start = models.DateField(
        help_text='First day of classes.  See <a href="http://umanitoba.ca/calendar">the UofM calendar / Academic Schedule</a> for dates.'
    )
    finish = models.DateField(help_text="Last day of classes.")

    objects = SemesterDateRangeManager()

    class Meta:
        ordering = ["start", "finish"]
        base_manager_name = "objects"

    def __str__(self):
        if self.is_plural():
            return self.start.strftime("%B %d") + " – " + self.finish.strftime("%B %d")
        else:
            return self.start.strftime("%B %d")

    def is_plural(self):
        return self.start != self.finish


#################################################################


@python_2_unicode_compatible
class Section(ClassesBaseModel):
    """
    A section is the record of a particular course during a particular
    semester, which meets in a particular timeslot.

    Meeting information is handled by the SectionSchedule object.
    """

    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, limit_choices_to={"active": True}
    )
    section_name = models.CharField(max_length=4)
    section_type = models.CharField(
        max_length=2,
        choices=conf.get("section_type:choices"),
        default=conf.get("section_type:default"),
    )
    slug = models.SlugField(
        unique=True, help_text="A url fragment which identies this section"
    )

    crn = models.CharField(
        max_length=10, verbose_name="CRN"
    )  # NOTE: CRN's are only unique within a Term.
    note = models.CharField(
        max_length=512,
        blank=True,
        help_text="Additional section information or details, e.g., for topics courses",
    )

    instructor = models.ForeignKey(
        "people.Person",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"active": True, "flags__slug": "instructor"},
        help_text='Only people with the "instructor" flag are shown',
    )
    additional_instructors = models.ManyToManyField(
        "people.Person",
        blank=True,
        limit_choices_to={"active": True, "flags__slug": "instructor"},
        related_name="additional_instructor_section",
        help_text='Only people with the "instructor" flag are shown',
    )
    override_instructor = models.BooleanField(
        default=False,
        help_text="If this is set, then the instructor will not be changed by any automatic update",
    )
    term = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        limit_choices_to={"active": True, "advertised": True},
    )

    objects = SectionManager()

    class Meta:
        ordering = ["term", "course", "section_name"]
        base_manager_name = "objects"

    def __str__(self):
        result = "{} {}".format(self.course.label, self.section_name)
        if self.instructor:
            result += ": {}".format(self.instructor)
        return result

    def get_absolute_url(self):
        return reverse("classes-section-detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        st = conf.get("section_type:on_save")(self)
        if st is not None:
            self.section_type = st
        return super(Section, self).save(*args, **kwargs)

    def get_instructor(self):
        """
        Figure out who the instructor is.
        """
        if not self.override_instructor and not self.instructor:
            instructor = self.sectionschedule_set.active().instructor()
            if instructor is not None:
                self.instructor = instructor
                self.save()
        return self.instructor

    def registration(self):
        """
        Returns the most recent actual registration, if any
        """
        try:
            return self.enrollment_set.latest().registration
        except Enrollment.DoesNotExist:
            pass

    def capacity(self):
        """
        Returns the most recent capacity, if any
        """
        try:
            return self.enrollment_set.latest().capacity
        except Enrollment.DoesNotExist:
            pass

    def waitlist_registration(self):
        """
        Returns the most recent actual registration, if any
        """
        try:
            return self.enrollment_set.latest().waitlist_registration
        except Enrollment.DoesNotExist:
            pass

    def waitlist_capacity(self):
        """
        Returns the most recent capacity, if any
        """
        try:
            return self.enrollment_set.latest().waitlist_capacity
        except Enrollment.DoesNotExist:
            pass

    def get_enrollment_by_date(self, date=None):
        try:
            if date is None:
                return self.enrollment_set.latest()
            else:
                return self.enrollment_set.filter(created__lte=date).latest()
        except Enrollment.DoesNotExist:
            pass

    def get_course_outline(self):
        """
        Returns the corresponding course outline, if any.
        """
        return self.course.courseoutline_set.filter(active=True, term=self.term)

    def is_current(self, reference_date=None, grace=21):
        """
        Returns True if this section has any schedules
        containing the given reference_date.
        If reference_date is None, then today is used.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        A = reference_date
        B = A - datetime.timedelta(days=grace)
        qs = self.sectionschedule_set.filter(
            date_range__start__lte=A, date_range__finish__gte=B
        )
        return qs.exists()


#################################################################


@python_2_unicode_compatible
class ScheduleType(ClassesBaseModel):
    """
    Types of schedules, such as Lecture, Laboratory, etc.
    """

    name = models.CharField(max_length=64)
    ordering = models.PositiveSmallIntegerField(default=50)

    class Meta:
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name


#################################################################


@python_2_unicode_compatible
class SectionSchedule(ClassesBaseModel):
    """
    Meeting time(s)/location(s) for a section.
    """

    date_range = models.ForeignKey(
        SemesterDateRange, on_delete=models.SET_NULL, null=True, blank=True
    )
    timeslot = models.ForeignKey(
        Timeslot, on_delete=models.PROTECT, limit_choices_to={"active": True}
    )
    room = models.ForeignKey(
        "places.ClassRoom", on_delete=models.PROTECT, limit_choices_to={"active": True}
    )
    override_room = models.BooleanField(
        default=False,
        help_text="If this is set, then the room will not be changed by any automatic update",
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, limit_choices_to={"active": True}
    )
    type = models.ForeignKey(
        ScheduleType, on_delete=models.PROTECT, limit_choices_to={"active": True}
    )
    instructor = models.ForeignKey(
        "people.Person",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"active": True, "flags__slug": "instructor"},
        help_text='Only people with the "instructor" flag are shown',
    )
    additional_instructors = models.ManyToManyField(
        "people.Person",
        blank=True,
        limit_choices_to={"active": True, "flags__slug": "instructor"},
        related_name="additional_instructor_sectionschedule",
        help_text='Only people with the "instructor" flag are shown',
    )
    override_instructor = models.BooleanField(
        default=False,
        help_text="If this is set, then the instructor will not be changed by any automatic update",
    )

    objects = SectionScheduleManager()

    class Meta:
        ordering = ["section", "date_range", "type"]
        base_manager_name = "objects"

    def __str__(self):
        return "{} schedule for {}".format(self.type, self.section)

    def vevent_list(self, for_print=False, include_section_events=True):
        """
        Return the vevent object list for all classes in this section.
        This specifically DOES NOT take into account cancelled classes,
            midterm, final exam, due dates, or office hours UNLESS
            ``include_section_events`` is ``True`` and there is something
            else that the calendar generator can use.
        """
        cal = vobject.iCalendar()
        if not self.active:
            return []
        if not self.section.active:
            return []
        if not self.section.course.active:
            return []
        if not self.section.course.department.active:
            return []

        def _get_class_schedule():
            if self.timeslot.name.lower() == "none":
                return []
            if not self.date_range:
                return []

            term_dtstart = utils.blend_date_and_time(
                self.date_range.start, self.timeslot.start_time
            )
            term_dtfinish = utils.blend_date_and_time(
                self.date_range.finish, self.timeslot.start_time
            )

            rrs = dateutil.rrule.rruleset()
            for impdate in ImportantDate.objects.filter(
                active=True,
                date__gte=self.date_range.start,
                date__lte=self.date_range.finish,
                no_class=True,
            ):
                dt = utils.blend_date_and_time(impdate.date, self.timeslot.start_time)
                rrs.exdate(dt)
                if impdate.end_date is not None:
                    enddt = utils.blend_date_and_time(
                        impdate.end_date, datetime.time(hour=23, minute=59, second=59)
                    )
                    while dt <= enddt:
                        dt += datetime.timedelta(days=1)
                        rrs.exdate(dt)
            term = dateutil.rrule.rrule(
                dateutil.rrule.WEEKLY,  # count=26,
                wkst=dateutil.rrule.SU,
                byweekday=self.timeslot.get_rrule_days(),
                dtstart=term_dtstart,
            )
            rrs.rrule(term)

            for dtstart in rrs.between(term_dtstart, term_dtfinish, inc=True):
                ev = cal.add("vevent")
                ev.add("dtstamp").value = dtstart
                ev.add("dtstart").value = dtstart
                ev.add("dtend").value = utils.blend_date_and_time(
                    datetime.date(*(dtstart.timetuple()[:3])), self.timeslot.stop_time
                )
                if not for_print:
                    ev.add("location").value = "{}".format(self.room)
                if for_print:
                    summary = (
                        self.section.course.label
                        + " "
                        + self.section.section_name
                        + " "
                        + self.lab_section_name
                    )
                    if self.instructor:
                        summary += " " + self.section.instructor.cn
                    ev.add("summary").value = summary
                else:
                    ev.add("summary").value = "{}".format(self.section)
            return cal.vevent_list if cal.vevent_list is not None else []

        def _get_related_events():
            # include other section events
            if not include_section_events:
                return []
            # add events of objects that relate to this object
            related_sets = [
                attr
                for attr in dir(self.section)
                if attr.endswith("_set") and attr != "sectionschedule_set"
            ]
            for attr in related_sets:
                related = getattr(self.section, attr)
                if hasattr(related.model, "vevent"):
                    for subobj in related.all():
                        ev = subobj.vevent()
                        if ev is not None:
                            cal.add(ev)
                if hasattr(related.model, "vevent_list"):
                    for subobj in related.all():
                        for ev in subobj.vevent_list():
                            cal.add(ev)

        _get_class_schedule()
        _get_related_events()
        return getattr(cal, "vevent_list", [])


#################################################################


@python_2_unicode_compatible
class CourseHandout(ClassesBaseModel):
    """
    Course handouts.
    Any file associated with a particular **course** (content
    DOES NOT CHANGE from section to section), usually a course outline
    (i.e., course contents document).
    """

    PUBLIC_CHOICES = ((True, "Public"), (False, "Restricted"))

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        limit_choices_to={
            "active": True,
            "department__active": True,
            "department__advertised": True,
        },
    )
    label = models.CharField(
        max_length=128, default="course content", help_text="Use lower case"
    )
    ordering = models.PositiveSmallIntegerField(default=10)
    path = models.FileField(
        upload_to=conf.get("course_outlines:upload_to"),
        storage=conf.get("course_outlines:storage"),
    )
    public = models.BooleanField(default=True, choices=PUBLIC_CHOICES)

    objects = CourseHandoutManager()

    class Meta:
        ordering = ["course", "ordering", "label"]
        base_manager_name = "objects"

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return self.path.url

    @property
    def coursename_label_capfirst(self):
        """
        Include the course label, section name, and course name; as  well as the
        ``capfirst`` label for this handout.
        """
        caplabel = capfirst(self.label)
        return "{self.course.label} - {self.course.name}: {caplabel}".format(
            self=self, caplabel=caplabel
        )

    @property
    def coursename_label_title(self):
        """
        Include the course label and course name; as  well as the
        ``title`` label for this handout.
        """
        title_label = title(self.label)
        return "{self.course.label} - {self.course.name}: {title_label}".format(
            self=self, title_label=title_label
        )


#################################################################


@python_2_unicode_compatible
class SectionHandout(ClassesBaseModel):
    """
    Section handouts.
    Any file associated with a particular section, usually a syllabus
    or other specific handout.
    """

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        limit_choices_to={
            "active": True,
            "course__active": True,
            "course__department__active": True,
            "course__department__advertised": True,
        },
    )
    label = models.CharField(
        max_length=128, default="syllabus", help_text="Use lower case"
    )
    ordering = models.PositiveSmallIntegerField(default=10)
    path = models.FileField(
        upload_to=conf.get("course_outlines:upload_to"),
        storage=conf.get("course_outlines:storage"),
    )

    objects = SectionHandoutManager()

    class Meta:
        ordering = ["section", "ordering", "label"]
        base_manager_name = "objects"

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return self.path.url

    @property
    def coursename_label_capfirst(self):
        """
        Include the course label, section name, and course name; as  well as the
        ``capfirst`` label for this handout.
        """
        caplabel = capfirst(self.label)
        return "{self.section.course.label} {self.section.section_name} - {self.section.course.name}: {caplabel}".format(
            self=self, caplabel=caplabel
        )

    @property
    def sectionname_label_capfirst(self):
        """
        Include the course label and section name; as  well as the
        ``capfirst`` label for this handout.
        """
        caplabel = capfirst(self.label)
        return "{self.section.course.label} {self.section.section_name}: {caplabel}".format(
            self=self, caplabel=caplabel
        )

    @property
    def coursename_label_title(self):
        """
        Include the course label, section name, and course name; as  well as the
        ``title`` label for this handout.
        """
        title_label = title(self.label)
        return "{self.section.course.label} {self.section.section_name} - {self.section.course.name}: {title_label}".format(
            self=self, title_label=title_label
        )

    @property
    def sectionname_label_title(self):
        """
        Include the course label and section name; as  well as the
        ``title`` label for this handout.
        """
        title_label = title(self.label)
        return "{self.section.course.label} {self.section.section_name}: {title_label}".format(
            self=self, title_label=title_label
        )


#################################################################


@python_2_unicode_compatible
class ImportantDate(ClassesBaseModel):
    """
    Important Dates which impact the schedule of courses.
    """

    date = models.DateField(
        help_text='See <a href="http://umanitoba.ca/calendar">the UofM calendar / Academic Schedule</a>, <a href="http://umanitoba.ca/student/records/deadlines/">student records</a> and and <a href="http://umanitoba.ca/summer">Summer Session / Important Dates</a> for dates.'
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Specify the end date for things like reading week, which last for more than one day.",
    )
    title = models.CharField(max_length=250)

    no_class = models.BooleanField(default=False)
    university_closed = models.BooleanField(default=False)

    objects = ImportantDateManager()

    class Meta:
        ordering = ["date"]

    def __str__(self):
        if self.end_date is not None:
            return "{} to {}: {}".format(self.date, self.end_date, self.title)
        return "{}: {}".format(self.date, self.title)

    def vevent(self):
        if not self.active:
            return None
        ev = vobject.icalendar.RecurringComponent("vevent")
        t = datetime.time(hour=0, minute=0, second=0)
        dtstart = utils.blend_date_and_time(self.date, t)
        ev.add("dtstamp").value = calfmt.format(dtstart)
        ev.add("dtstart").value = calfmt.format_date(dtstart)
        ev.dtstart.value_param = "DATE"
        if self.end_date is not None:
            dtend = utils.blend_date_and_time(self.end_date, t) + datetime.timedelta(
                days=+1
            )
            ev.add("dtend").value = calfmt.format_date(dtend)
            ev.dtend.value_param = "DATE"
            # spec says we only include DTEND when it's a multi-day
            #   event.

        desc = []
        if self.no_class:
            desc.append("no classes")
        if self.university_closed:
            desc.append("university closed")
        if desc:
            ev.add("description").value = ", ".join(desc).capitalize()
        summary = self.title
        if desc:
            summary += " – " + desc[-1].title()
        ev.add("summary").value = summary
        return ev

    def _date_to_dt(self, date, hour=0, minute=0, second=0, tzinfo=None):
        """
        Convert a date to a datetime, with given hour, minute, and second
        values.  If tzinfo is None, then use assume the current timezone.
        Always return in UTC.

        This is tricky, because really one *day* in this context refers to
        a datetime interval from Midnight to Midnight
        *in a particular timezone*.
        I assume that this is the current timezone, although to be
        truly general each object should store its timezone as well.
        The problem here is that dates are a *calendar concept* whereas
        events (datetimes) refer to a specific point in time
        which does not change.

        """
        if tzinfo is None:
            tzinfo = get_current_timezone()
        naive = datetime.datetime(date.year, date.month, date.day, hour, minute, second)
        aware = tzinfo.localize(naive)
        return utc.normalize(aware.astimezone(utc))

    @property
    def dtstart(self):
        return self._date_to_dt(self.date)

    @property
    def dtend(self):
        d = self.date if self.end_date is None else self.end_date
        return self._date_to_dt(d, 23, 59, 59)

    def twitter_dtlist(self):
        """
        Return a list of suggested datetimes for tweeting this information.
        """
        if now() > self.dtstart:
            # Don't tweet about things which are already past or started.
            return []
        return [
            self.dtstart - datetime.timedelta(days=1),
            self.dtstart - datetime.timedelta(days=7),
        ]


#################################################################


@python_2_unicode_compatible
class Enrollment(ClassesBaseModel):
    """
    The enrolment for a section on a particular date.
    The idea here is to provide many enrolment entries (a time series)
    for a single section.
    """

    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, limit_choices_to={"active": True}
    )
    capacity = models.IntegerField()
    registration = models.IntegerField(verbose_name="Actual registration")
    waitlist_capacity = models.IntegerField(default=0)
    waitlist_registration = models.IntegerField(default=0)

    class Meta:
        get_latest_by = "created"

    def __str__(self):
        return "{self.registration}".format(self=self)


#################################################################
#################################################################
