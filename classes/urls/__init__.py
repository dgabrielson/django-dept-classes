"""
Default url pattern for the classes application.
"""
#######################
from __future__ import print_function, unicode_literals

#######################
from django.conf.urls import include, url
from django.views.generic import TemplateView
from webcal import views as webcal_views

from .. import views
from ..feeds import ImportantDatesFeed
from ..models import ImportantDate, Section, SectionHandout

urlpatterns = [
    url(
        r"^$",
        TemplateView.as_view(template_name="classes/index.html"),
        name="classes-index",
    ),
    url(r"^list/$", views.advertised_course_list, name="classes-adv-course-list"),
    url(r"^current/$", views.advertised_section_list, name="classes-adv-section-list"),
    url(r"^department/$", views.department_list, name="classes-department-list"),
    url(
        r"^department/(?P<slug>[\w-]+)/$",
        views.department_detail,
        name="classes-department-detail",
    ),
    url(r"^semester/$", views.semester_list, name="classes-semester-list"),
    url(
        r"^section-semester/$",
        views.section_semester_list,
        name="classes-section-semester-list",
    ),
    url(
        r"^semester/timetable/(?P<slug>[\w-]+)/$",
        views.semester_print_timetable,
        name="classes-semester-timetable",
    ),
    url(
        r"^semester/timetable/(?P<slug>[\w-]+)/labs/$",
        views.semester_print_timetable_labs,
        name="classes-semester-timetable-labs",
    ),
    url(
        r"^semester/timetable/(?P<slug>[\w-]+)/lectures/$",
        views.semester_print_timetable_lectures,
        name="classes-semester-timetable-lectures",
    ),
    url(
        r"^semester/(?P<slug>[\w-]+)/$",
        views.semester_detail,
        name="classes-semester-detail",
    ),
    url(
        r"^section-semester/(?P<slug>[\w-]+)/$",
        views.section_semester_detail,
        name="classes-section-semester-detail",
    ),
    url(r"^section/$", views.section_list, name="classes-section-list"),
    url(
        r"^section/(?P<slug>[\w-]+)/$",
        views.section_detail,
        name="classes-section-detail",
    ),
    url(r"^instructor/$", views.instructor_list, name="classes-instructor-list"),
    url(
        r"^instructor/(?P<slug>[\w-]+)/$",
        views.instructor_detail,
        name="classes-instructor-detail",
    ),
    #     url(r'^department/(?P<dept_code>[\w-]+)/(?P<slug>[\w-]+)/$',
    #         views.department_course_detail',
    #         name='classes-department-course-detail',
    #         ),
    url(r"^outlines/$", views.advertised_handout_list, name="classes-outline-list"),
    url(
        r"^outlines/by-course/$",
        views.SectionHandoutDrilldownByCourse.as_view(
            template_name="classes/sectionhandout_by_course.html"
        ),
        name="classes-outline-by-course",
    ),
    url(
        r"^outlines/by-course/(?P<slug>[\w-]+)/$",
        views.SectionHandoutDrilldownByCourse.as_view(
            template_name="classes/sectionhandout_by_course_selected.html"
        ),
        name="classes-outline-by-course-selected",
    ),
    url(
        r"^outlines/by-term/$",
        views.SectionHandoutDrilldownByTerm.as_view(
            template_name="classes/sectionhandout_by_semester.html"
        ),
        name="classes-outline-by-term",
    ),
    url(
        r"^outlines/by-term/(?P<slug>[\w-]+)/$",
        views.SectionHandoutDrilldownByTerm.as_view(
            template_name="classes/sectionhandout_by_semester_selected.html"
        ),
        name="classes-outline-by-term-selected",
    ),
    url(r"^outlines/all/$", views.all_handout_list, name="classes-outline-list-all"),
    url(
        r"^(?P<course_slug>[\w-]+)/(?P<term_slug>[\w-]+)/$",
        views.semester_course_detail,
        name="classes-semester-course-detail",
    ),
    url(r"^(?P<slug>[\w-]+)/$", views.course_details, name="classes-course-detail"),
    url(
        r"^(?P<slug>[\w-]+)/graph.svg$",
        views.CoursePrereqSvgView.as_view(),
        name="classes-course-prereq-svg",
    ),
    # url(
    #     r'^(?P<slug>[\w-]+)/graph.dot$',
    #     views.CoursePrereqDotSrcView.as_view(),
    #     name='classes-course-prereq-dotsrc',
    # ),
    url(
        r"^course-map-legend.svg$",
        views.CoursePrereqSvgLegendView.as_view(),
        name="classes-course-prereq-svg-legend",
    ),
    url(
        r"^course-list.svg$",
        views.CourseListSvgView.as_view(),
        name="classes-course-list-svg",
    ),
    url(
        r"^important-dates/feed/$",
        ImportantDatesFeed(),
        name="classes-important-dates-feed",
    ),
    # CLASS CALENDARS:
    url(
        r"^calendar/important-dates$",
        webcal_views.generic_queryset_icalendar,
        kwargs={
            "queryset": ImportantDate.objects.active(),
            "include_set_events": False,
        },
        name="classes-calendar-important-dates",
    ),
    url(
        r"^calendar/section/(?P<object_id>\d+)$",
        webcal_views.generic_object_icalendar,
        kwargs={"queryset": Section.objects.all(), "include_set_events": False},
        name="classes-calendar-section",
    ),
    url(r"^calendar/instr/(?P<slug>[\w-]+)$", views.calendar_redirect),
    url(r"^calendar/instr/(?P<slug>[\w-]+)/$", views.calendar_redirect),
    url(r"^api/", include("classes.api.urls")),
]
