"""
Activate in your template by putting
{% load dept_classes %}
near the top.

Available Filters:
course_autolink    - auto-link DEPT wxyz to active course pages.

"""
#######################
from __future__ import print_function, unicode_literals

import re

from classes.models import Course, Semester
from django import template
from django.urls import reverse
from django.utils.timezone import now

#######################
#####################################################################

#####################################################################

register = template.Library()

#####################################################################


@register.filter
def course_autolink(text):
    """
    Returns a new string with all occurances of DEPT WXYZ that match
    a statistics course being linked to the course info page for
    that course.

    Usage: {{ string|courselink }}
    """
    courses = Course.objects.advertised().select_related("department")
    slug_map = dict([(course.label, course.slug) for course in courses])
    result = text
    for key in slug_map:
        if key in text:
            value = '<a href="%s">%s</a>' % (
                reverse("classes-course-detail", args=[slug_map[key]]),
                key,
            )
            result = result.replace(key, value)
    return result


course_autolink.is_safe = True

#####################################################################


@register.simple_tag(takes_context=True)
def get_advertised_semesters(context, save_as=None, max_count=None):
    """
    {% get_advertised_semesters %} -> qs
    {% get_advertised_semesters 'upcoming_exams_qs' %}
    """
    qs = Semester.objects.advertised()
    if max_count is not None:
        qs = qs[:max_count]
    if save_as is not None:
        context[save_as] = qs
        return ""
    return qs


################################################################


@register.filter
def get_enrollment_by_date(section, date):
    return section.get_enrollment_by_date(date)


################################################################


@register.filter
def list_with_prev(l):
    """
    {% for curr, prev in my_list|list_with_prev %}
        ...
    {% endfor %}
    """
    return zip(l, [None] + l)


################################################################


@register.filter
def historical_sections(obj, years, dt=None):
    """
    Specialized regroup
    """
    years = int(years)
    section_qs = obj.section_set.historical(reference_date=dt)
    if dt is None:
        dt = now()
    end_dt = dt.replace(year=dt.year + years)
    if end_dt < dt:
        dt, end_dt = end_dt, dt
    term_qs = list(Semester.objects.filter_by_date_range(dt, end_dt))
    # correct for the "last" term
    if years < 0:
        term_qs = term_qs[1:]
    else:
        term_qs = term_qs[:-1]
    section_qs = section_qs.filter(term__in=term_qs)
    return section_qs


################################################################
