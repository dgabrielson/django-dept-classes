from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from ..models import Course, Enrollment, Section, Semester


class EnrollmentForTerm(ListView):
    """
    A List of enrollment information for the term
    """

    model = Enrollment

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        course_slug = self.kwargs.get("course_slug")
        term_slug = self.kwargs.get("term_slug")
        if course_slug is None or term_slug is None:
            raise Http404
        qs = qs.filter(section__term__slug=term_slug, section__course__slug=course_slug)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["course"] = get_object_or_404(
            Course, slug=self.kwargs.get("course_slug")
        )
        context["term"] = get_object_or_404(Semester, slug=self.kwargs.get("term_slug"))
        context["section_list"] = Section.objects.filter(
            course=context["course"], term=context["term"]
        ).active()
        return context
