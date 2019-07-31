from django.contrib.auth.decorators import login_required, permission_required
from django.urls import path
from django.views.generic import DetailView, ListView

from ..models import Course
from ..views import private as private_views

urlpatterns = [
    path(
        "",
        permission_required("classes.view_course")(
            ListView.as_view(
                queryset=Course.objects.active().filter(department__advertised=True),
                template_name="classes/private/course_list.html",
            )
        ),
        name="classes-restricted-course-list",
    ),
    path(
        "<slug>/",
        permission_required("classes.view_course")(
            DetailView.as_view(
                queryset=Course.objects.active(),
                template_name="classes/private/course_detail.html",
            )
        ),
        name="classes-restricted-course-detail",
    ),
    path(
        "<slug>/docs/",
        permission_required("classes.view_course")(
            DetailView.as_view(
                queryset=Course.objects.active(),
                template_name="classes/private/course_handouts.html",
            )
        ),
        name="classes-restricted-course-handouts",
    ),
    path(
        "<slug>/exams/",
        permission_required("classes.view_course")(
            DetailView.as_view(
                queryset=Course.objects.active(),
                template_name="classes/private/course_exams.html",
            )
        ),
        name="classes-restricted-course-exams",
    ),
    path(
        "<slug>/enrollment/",
        permission_required("classes.view_course")(
            DetailView.as_view(
                queryset=Course.objects.active(),
                template_name="classes/private/course_enrollment.html",
            )
        ),
        name="classes-restricted-course-enrollment",
    ),
    path(
        "<course_slug>/enrollment/<term_slug>/",
        permission_required("classes.view_course")(
            private_views.EnrollmentForTerm.as_view(
                template_name="classes/private/course_enrollment_for_term.html"
            )
        ),
        name="classes-restricted-course-enrollment-term",
    ),
]
