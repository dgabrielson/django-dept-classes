"""
Views for the classes application.
"""
#######################################################################

from __future__ import print_function, unicode_literals

import datetime

import graphviz  # could be replace with subprocess call.
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from latex.djangoviews import LaTeXDetailView, LaTeXListView

from .. import conf
from ..models import (
    Course,
    Department,
    Requisite,
    Section,
    SectionHandout,
    SectionSchedule,
    Semester,
)
from ..utils.print_timetable import latex_tabular_list

#######################################################################


class DepartmentMixin(object):
    """
    Mixin for Department views.
    """

    queryset = Department.objects.public()


#######################################################################


class DepartmentListView(DepartmentMixin, ListView):
    """
    List of Department objects.
    """


department_list = DepartmentListView.as_view()

#######################################################################


class DepartmentDetailView(DepartmentMixin, DetailView):
    """
    Details on a particular Department object.
    """


department_detail = DepartmentDetailView.as_view()

#######################################################################


class SemesterMixin(object):
    """
    Mixin for Department views.
    """

    queryset = Semester.objects.active()


#######################################################################


class SemesterListView(SemesterMixin, ListView):
    """
    List of Semester objects.
    """


semester_list = SemesterListView.as_view()

#######################################################################


class SectionSemesterListView(SemesterListView):
    """
    List of Semester objects.
    """

    template_name = "classes/section_semester_list.html"


section_semester_list = SectionSemesterListView.as_view()

#######################################################################


class AdvertisedSemesterListView(SemesterMixin, ListView):
    """
    List of Semester objects.
    """

    queryset = Semester.objects.active().advertised()


advertised_semester_list = AdvertisedSemesterListView.as_view()

#######################################################################


class SemesterDetailView(SemesterMixin, DetailView):
    """
    Details on a particular Semester.
    """


semester_detail = SemesterDetailView.as_view()

#######################################################################


class SectionSemesterDetailView(SemesterDetailView):
    """
    Details on a particular Semester.
    """

    template_name = "classes/section_semester_detail.html"


section_semester_detail = SectionSemesterDetailView.as_view()

#######################################################################


class SectionMixin(object):
    """
    Mixin for Section views.
    """

    queryset = Section.objects.active_terms()


#######################################################################


class SemesterCourseDetailView(SectionMixin, ListView):
    """
    List of sections -- for a particular term and course.
    """

    template_name = "classes/semester_course_detail.html"

    def get_queryset(self):
        term_slug = self.kwargs.get("term_slug", None)
        course_slug = self.kwargs.get("course_slug", None)
        qs = Section.objects.active().filter(
            course__slug=course_slug, term__slug=term_slug
        )
        qs = qs.select_related("course", "course__department", "instructor")
        # NB: all prefetch_related() attempts increase total time.
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super(SemesterCourseDetailView, self).get_context_data(
            *args, **kwargs
        )
        term_slug = self.kwargs.get("term_slug", None)
        course_slug = self.kwargs.get("course_slug", None)
        course = get_object_or_404(Course, active=True, slug=course_slug)
        semester = get_object_or_404(Semester, active=True, slug=term_slug)
        context.update({"course": course, "semester": semester})
        return context


semester_course_detail = SemesterCourseDetailView.as_view()

#######################################################################


class SectionListView(SectionMixin, ListView):
    """
    List of Section objects.
    """


section_list = SectionListView.as_view()

#######################################################################


class SectionDetailView(SectionMixin, DetailView):
    """
    Details on a particular Section.
    """


section_detail = SectionDetailView.as_view()

#######################################################################


class SectionScheduleFKMixin(object):
    """
    Mixin for ClassRoom views.
    """

    app_label = "classes"
    original_label = "(set this)"
    object_name = "(set this)"
    fk_field_name = "(set this)"

    def get_queryset(self):
        model = apps.get_model(self.original_label, self.object_name)
        pk_set = set(
            SectionSchedule.objects.active_terms().values_list(
                self.fk_field_name, flat=True
            )
        )
        # TODO augment with associated section schedules.
        qs = model.objects.filter(pk__in=pk_set)
        return qs.filter(active=True)

    def get_template_names(self):
        names = []
        names.append(
            "{0}/{1}{2}.html".format(
                self.app_label, self.object_name.lower(), self.template_name_suffix
            )
        )
        names += super(SectionScheduleFKMixin, self).get_template_names()
        return names


#######################################################################


class InstructorMixin(SectionScheduleFKMixin):
    """
    Mixin for Instructor views.
    """

    original_label = "people"
    object_name = "Person"
    fk_field_name = "instructor"


#######################################################################


class InstructorListView(InstructorMixin, ListView):
    """
    List of Instructor objects.
    """


instructor_list = InstructorListView.as_view()

#######################################################################


class InstructorDetailView(InstructorMixin, DetailView):
    """
    Details on a particular Instructor.
    """


instructor_detail = InstructorDetailView.as_view()

#######################################################################


class ClassRoomMixin(SectionScheduleFKMixin):
    """
    Mixin for ClassRoom views.
    """

    original_label = "places"
    object_name = "ClassRoom"
    fk_field_name = "location"


#######################################################################


class ClassRoomListView(ClassRoomMixin, ListView):
    """
    List of ClassRoom objects.
    """


classroom_list = ClassRoomListView.as_view()

#######################################################################


class ClassRoomDetailView(ClassRoomMixin, DetailView):
    """
    Details on a particular ClassRoom.
    """


classroom_detail = ClassRoomDetailView.as_view()

#######################################################################


class CourseDetailView(DetailView):

    queryset = Course.objects.active().select_related("department")
    template_name = "classes/course_detail.html"
    context_object_name = "course"

    def get_object(self):
        if "slug" in self.kwargs:
            slug = self.kwargs["slug"]
        else:
            raise ImproperlyConfigured(
                "Either a slug or a course_number is required for CourseDetail_View"
            )
        try:
            obj = Course.objects.get_by_slug(slug)
        except Course.DoesNotExist:
            raise Http404("Course not found")
        return obj


course_details = CourseDetailView.as_view()

#######################################################################


class GraphvizTemplateResponse(TemplateResponse):

    engine = "dot"
    format = "svg"
    renderer = None
    formatter = None

    @property
    def rendered_content(self):
        source = super().rendered_content
        return graphviz.pipe(
            self.engine,
            self.format,
            source.encode("utf-8"),
            renderer=self.renderer,
            formatter=self.formatter,
        )


class CoursePrereqDotSrcView(DetailView):

    queryset = Course.objects.active()
    template_name = "classes/course_prereq_map.dot"
    content_type = "text/vnd.graphviz"


class CoursePrereqSvgView(CoursePrereqDotSrcView):

    response_class = GraphvizTemplateResponse
    content_type = "image/svg+xml"


def course_graphviz_svg_data(course):
    gtr = GraphvizTemplateResponse(
        None, "classes/course_prereq_map.dot", {"course": course}
    )
    gtr.render()
    return gtr.content


#######################################################################


class CoursePrereqSvgLegendView(TemplateView):
    template_name = "classes/course_prereq_legend.dot"
    response_class = GraphvizTemplateResponse
    content_type = "image/svg+xml"


#######################################################################


class CourseListSvgView(ListView):

    queryset = Course.objects.active().filter(department__advertised=True)
    template_name = "classes/course_list.dot"
    response_class = GraphvizTemplateResponse
    content_type = "image/svg+xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["ranked_requisites"] = Requisite.objects.ranked().active()
        return context


#######################################################################


class CourseListView(ListView):
    queryset = Course.objects.active().filter(department__public=True)


course_list = CourseListView.as_view()

#######################################################################


class AdvertisedCourseListView(ListView):
    queryset = Course.objects.active().filter(
        department__public=True, department__advertised=True
    )


advertised_course_list = AdvertisedCourseListView.as_view()

#######################################################################


class AdvertisedSectionListView(ListView):

    queryset = Section.objects.filter(
        active=True, course__department__advertised=True, term__advertised=True
    ).select_related("course", "course__department", "term")
    template_name = "classes/section_list.html"


advertised_section_list = AdvertisedSectionListView.as_view()

#######################################################################


class HandoutContextMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        sectionhandout_title = conf.get("sectionhandout:title")
        sectionhandout_title_plural = (
            conf.get("sectionhandout:title:plural") or sectionhandout_title + "s"
        )
        coursehandout_title = conf.get("coursehandout:title")
        coursehandout_title_plural = (
            conf.get("coursehandout:title:plural") or coursehandout_title + "s"
        )

        context["sectionhandout_title"] = sectionhandout_title
        context["sectionhandout_title_plural"] = sectionhandout_title_plural
        context["coursehandout_title"] = coursehandout_title
        context["coursehandout_title_plural"] = coursehandout_title_plural

        return context


########################################################################


class SectionHandoutListView(HandoutContextMixin, ListView):

    queryset = SectionHandout.objects.filter(active=True).order_by(
        "-section__term", "section", "ordering", "label"
    )


all_handout_list = SectionHandoutListView.as_view()

######################################################################


class AdvertisedSectionHandoutListView(SectionHandoutListView):

    queryset = SectionHandout.objects.filter(
        active=True,
        section__course__department__advertised=True,
        section__term__advertised=True,
    )


advertised_handout_list = AdvertisedSectionHandoutListView.as_view()

#######################################################################


class DrilldownMixin:

    drilldown_filter = "FOO__subattr__slug"
    filter_class = object
    filter_class_slug_field = "slug"

    def get_filter_object(self):
        slug = self.kwargs.get("slug", None)
        if slug is None:
            return None
        return get_object_or_404(
            self.filter_class, **{self.filter_class_slug_field: slug}
        )

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        slug = self.kwargs.get("slug", None)
        if slug is not None:
            queryset = queryset.filter(**{self.drilldown_filter: slug})
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["filter_object"] = self.get_filter_object()
        return context


#######################################################################


class CourseSortMixin:
    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        return queryset.order_by("section__course", "-section__term", "section")


#######################################################################


class SectionHandoutDrilldownByTerm(DrilldownMixin, SectionHandoutListView):
    drilldown_filter = "section__term__slug"
    filter_class = Semester


class SectionHandoutDrilldownByCourse(
    CourseSortMixin, DrilldownMixin, SectionHandoutListView
):
    drilldown_filter = "section__course__slug"
    filter_class = Course


#######################################################################


class CalendarRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, slug):
        if slug is not None:
            return "/people/%s/calendar" % slug


calendar_redirect = CalendarRedirectView.as_view()

#######################################################################


class PrintSemesterSchedule(LaTeXListView):
    """
    Produce the pdf for semester schedules.
    Note that this view is used by the admin interface.
    """

    queryset = Semester.objects.all()
    template_name = "classes/print/semester_schedule.tex"
    as_attachment = False

    # allow post to this view -- admin actions.
    # def post(self, *args, **kwargs):
    #    return self.get(*args, **kwargs)

    def get_queryset(self):
        """
        Get the actual queryset.
        """
        if "pk" in self.request.GET:
            selected = self.request.GET.getlist("pk")
            return self.queryset.filter(pk__in=selected)
        else:
            return self.queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if "date" in self.request.GET:
            date_str = self.request.GET.get("date")
            nd = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            dt = datetime.datetime.combine(nd, datetime.time(23, 59, 59))
            dt = timezone.make_aware(dt)
        else:
            dt = timezone.now()

        context.update({"date": dt, "enrolment_date_flag": "date" in self.request.GET})
        return context


#######################################################################


class PrintTimetable(LaTeXDetailView):
    """
    A quick view timetable of all advertised section schedules
    for a given semester.
    """

    queryset = Semester.objects.all()
    template_name = "classes/print/timetable.tex"
    as_attachment = False
    schedule_types = None

    def get_context_data(self, *args, **kwargs):
        context = super(PrintTimetable, self).get_context_data(*args, **kwargs)
        context.update(
            {
                "tabular_list": latex_tabular_list(
                    self.object, schedule_types=self.schedule_types
                )
            }
        )
        return context


semester_print_timetable = PrintTimetable.as_view()


class PrintTimetableLectures(PrintTimetable):
    schedule_types = ["Lecture", "Class"]


semester_print_timetable_lectures = PrintTimetableLectures.as_view()


class PrintTimetableLabs(PrintTimetable):
    schedule_types = ["Tutorial", "Laboratory", "Session"]


semester_print_timetable_labs = PrintTimetableLabs.as_view()

#######################################################################
#
