"""
Admin interfaces for the classes application.
"""
#######################
from __future__ import print_function, unicode_literals

from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.forms import ModelChoiceField, ModelMultipleChoiceField, TextInput
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .forms import CourseHandoutForm, SectionHandoutForm
from .models import (
    Course,
    CourseHandout,
    Department,
    ImportantDate,
    Prerequisite,
    Requisite,
    ScheduleType,
    Section,
    SectionHandout,
    SectionSchedule,
    Semester,
    SemesterDateRange,
    Timeslot,
)
from .views import PrintSemesterSchedule

#######################
##############################################################

# adaptive use of admin_export:
try:
    import admin_export
except ImportError:
    admin_export = None

##############################################################


class SectionLabelFromInstanceMixin(object):
    def label_from_instance(self, obj):
        label = "{} ({})".format(obj, obj.term)
        return label


class SectionAutocompleteJsonView(SectionLabelFromInstanceMixin, AutocompleteJsonView):
    """
    Additional imports::

from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.http import Http404, JsonResponse


    In a model admin derived class, use::

    def autocomplete_view(self, request):
        return LabelAutocompleteJsonView.as_view(model_admin=self)(request)

    """

    def get(self, request, *args, **kwargs):
        """
        Return a JsonResponse with search results of the form:
        {
            results: [{id: "123" text: "foo"}],
            pagination: {more: true}
        }
        """
        if not self.model_admin.get_search_fields(request):
            raise Http404(
                "%s must have search_fields for the autocomplete_view."
                % type(self.model_admin).__name__
            )
        if not self.has_perm(request):
            return JsonResponse({"error": "403 Forbidden"}, status=403)

        self.term = request.GET.get("term", "")
        self.paginator_class = self.model_admin.paginator
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse(
            {
                "results": [
                    {"id": str(obj.pk), "text": self.label_from_instance(obj)}
                    for obj in context["object_list"]
                ],
                "pagination": {"more": context["page_obj"].has_next()},
            }
        )


class SectionChoiceField(SectionLabelFromInstanceMixin, ModelChoiceField):
    pass


class SectionMultipleChoiceField(
    SectionLabelFromInstanceMixin, ModelMultipleChoiceField
):
    pass


##############################################################


class CourseLevelFilter(admin.SimpleListFilter):
    """
    A way of filter courses by their leading code digit;
    e.g., 1000-level 2000-level, etc.
    """

    title = "course code"
    parameter_name = "code-startswith"

    def lookups(self, request, model_admin):
        """
        return a list of (code, name) pairs.
        """
        qs = Course.objects.all()
        codes = qs.values_list("code", flat=True)
        leading_list = sorted(set(c[0] for c in codes))

        def _label(l):
            n = min([len(s) for s in codes if s.startswith(l)])
            return l + "*" * (n - 1)

        return [(l, _label(l)) for l in leading_list]

    def queryset(self, request, queryset):
        """
        Apply the filter value as stored in self.value()
        """
        if self.value():
            return queryset.filter(code__startswith=self.value())
        return queryset


##############################################################


class UsedValuesForeignKeyFilter(admin.SimpleListFilter):
    """
    A custom filter, so that we only see foreign key values which are used.
    """

    # Define a subclass and set these appropriately:
    title = "SetThis"
    parameter_name = "set_this__id__exact"
    field_name = "set_this"
    allow_none = True
    model = object

    def get_filter_name(self, obj):
        """
        Return the name of the object, as appropriate
        """
        return "{}".format(obj)

    def get_lookup_values_queryset(self, request, model_admin):
        """
        Return the related objects queryset to use for the filter.
        """
        qs = model_admin.get_queryset(request)
        pk_set = qs.values_list(self.field_name, flat=True).distinct()
        related_qs = self.model.objects.filter(pk__in=pk_set)
        return related_qs

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples (coded-value, title).
        """
        related_qs = self.get_lookup_values_queryset(request, model_admin)
        lookups = [(o.pk, self.get_filter_name(o)) for o in related_qs]
        if self.allow_none:
            lookups.append(("(None)", "(None)"))
        return lookups

    def queryset(self, request, queryset):
        """
        Apply the filter to the existing queryset.
        """
        filter = self.value()
        filter_field = self.field_name
        if filter is None:
            return
        elif filter == "(None)":
            filter_field += "__isnull"
            filter_value = True
        else:
            filter_field += "__pk__exact"
            filter_value = filter
        return queryset.filter(**{filter_field: filter_value}).distinct()


##############################################################


class CourseFilter(UsedValuesForeignKeyFilter):
    """
    The course filter only filters **advertised** department's courses
    which are in use.
    """

    title = "course"
    parameter_name = "course"
    field_name = "course"
    allow_none = False
    model = Course

    def get_filter_name(self, obj):
        """
        Return the name of the object, as appropriate
        """
        return obj.label

    def get_lookup_values_queryset(self, request, model_admin):
        """
        Return the related objects queryset to use for the filter.
        """
        qs = super(CourseFilter, self).get_lookup_values_queryset(request, model_admin)
        return qs.filter(department__advertised=True)


##############################################################


class SemesterFilter(UsedValuesForeignKeyFilter):
    title = "semester"
    parameter_name = "semester"
    field_name = "term"
    allow_none = False
    model = Semester

    def get_lookup_values_queryset(self, request, model_admin):
        """
        Return the related objects queryset to use for the filter.
        """
        qs = super(SemesterFilter, self).get_lookup_values_queryset(
            request, model_admin
        )
        return qs.reverse()


##############################################################


class SectionCourseFilter(CourseFilter):
    field_name = "section__course"


##############################################################


class SectionSemesterFilter(SemesterFilter):
    field_name = "section__term"


##############################################################


def mark_inactive(modeladmin, request, queryset):
    """
    Mark selected items as inactive
    """
    queryset.update(active=False)


mark_inactive.short_description = mark_inactive.__doc__.strip()

##############################################################


def mark_active(modeladmin, request, queryset):
    """
    Mark selected items as active
    """
    queryset.update(active=True)


mark_active.short_description = mark_active.__doc__.strip()

##############################################################


def mark_scheduled(modeladmin, request, queryset):
    """
    Mark selected items for use in scheduling
    """
    queryset.update(scheduled=True)


mark_scheduled.short_description = mark_scheduled.__doc__.strip()

##############################################################


class SectionScheduleInline(admin.StackedInline):
    model = SectionSchedule
    filter_horizontal = ["additional_instructors"]
    extra = 0


class SectionHandoutInline(admin.TabularInline):
    model = SectionHandout
    form = SectionHandoutForm
    extra = 0


class SectionAdmin(admin.ModelAdmin):
    actions = [mark_active, mark_inactive, "spreadsheet_semester_enrollment"]
    filter_horizontal = ["additional_instructors"]
    list_display = ["course", "section_name", "crn", "instructor", "term", "note"]
    list_filter = [
        "active",
        "term",
        "course__department",
        CourseFilter,
        "section_type",
        SemesterFilter,
    ]
    list_select_related = ["course", "course__department", "term", "instructor"]
    search_fields = [
        "section_name",
        "course__name",
        "course__code",
        "course__department__code",
        "course__department__name",
        "term__slug",
        "crn",
        "note",
    ]
    ordering = ["-term", "course", "section_name"]
    readonly_fields = ["section_type"]
    save_on_top = True

    inlines = [SectionHandoutInline, SectionScheduleInline]

    def get_actions(self, request):
        actions = super(SectionAdmin, self).get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        if admin_export is None and "spreadsheet_semester_enrollment" in actions:
            del actions["spreadsheet_semester_enrollment"]
        else:
            if "export_redirect_spreadsheet_xlsx" in actions:
                del actions["export_redirect_spreadsheet_xlsx"]
        return actions

    def spreadsheet_semester_enrollment(self, request, queryset):
        """
        Redirect to the actual view.
        """
        url = reverse_lazy("admin_export_spreadsheet")
        # this query is for the corresponding PKs of SectionSchedules
        pk_list = (
            SectionSchedule.objects.filter(section__in=queryset)
            .active()
            .values_list("pk", flat=True)
            .distinct()
        )
        query = "&".join(["pk={0}".format(s) for s in pk_list])
        query += "&format=xlsx"
        ct = ContentType.objects.get_for_model(SectionSchedule)
        query += "&contenttype={0}".format(ct.pk)
        return HttpResponseRedirect(url + "?" + query)

    spreadsheet_semester_enrollment.short_description = (
        "Generate XLSX schedule with enrollment"
    )

    def autocomplete_view(self, request):
        return SectionAutocompleteJsonView.as_view(model_admin=self)(request)


admin.site.register(Section, SectionAdmin)

##############################################################


class ScheduleTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "ordering"]


admin.site.register(ScheduleType, ScheduleTypeAdmin)

##############################################################


class CourseHandoutInline(admin.TabularInline):
    model = CourseHandout
    form = CourseHandoutForm
    extra = 0


class PrerequisiteInline(admin.TabularInline):
    model = Prerequisite
    extra = 0
    autocomplete_fields = ["requisite"]
    formfield_overrides = {
        models.CharField: {"widget": TextInput(attrs={"size": "10"})}
    }


class CourseAdmin(admin.ModelAdmin):
    autocomplete_fields = ["department"]
    actions = [mark_active, mark_inactive]
    list_display = ["label", "active", "name"]
    list_filter = ["active", "department", CourseLevelFilter]
    list_select_related = True
    save_on_top = True
    search_fields = ["department__code", "code", "name"]

    inlines = [CourseHandoutInline, PrerequisiteInline]


admin.site.register(Course, CourseAdmin)

##############################################################


class DepartmentAdmin(admin.ModelAdmin):
    actions = [mark_active, mark_inactive]
    list_display = ["name", "code", "slug", "advertised", "public"]
    list_filter = ["active", "advertised", "public"]
    prepopulated_fields = {"slug": ("code",)}
    search_fields = ["name", "code", "slug", "description"]


admin.site.register(Department, DepartmentAdmin)

##############################################################


class SemesterAdmin(admin.ModelAdmin):
    """
    Model admin for semester objects.
    Note the url extension and the PDF generator action.
    """

    actions = [
        mark_active,
        mark_inactive,
        "print_semester_schedule",
        "print_semester_enrollment",
        "spreadsheet_semester_enrollment",
    ]
    list_display = ["__str__", "slug", "is_current_tag", "advertised"]
    list_filter = ["active", "advertised", "year", "term"]
    ordering = ["-year", "-term"]
    readonly_fields = ["year", "term", "slug"]  # No changes.

    def get_actions(self, request):
        actions = super(SemesterAdmin, self).get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        if admin_export is None:
            del actions["spreadsheet_semester_enrollment"]
        else:
            if "export_redirect_spreadsheet_xlsx" in actions:
                del actions["export_redirect_spreadsheet_xlsx"]
        return actions

    def get_urls(self):
        """
        Extend the admin urls for this model.
        Provide a link by subclassing the admin change_form,
        and adding to the object-tools block.
        """
        urls = super(SemesterAdmin, self).get_urls()
        urls = [
            url(
                r"^print-schedule/$",
                self.admin_site.admin_view(PrintSemesterSchedule.as_view()),
                name="classes-semester-print-schedule",
            ),
            url(
                r"^print-enrollment/$",
                self.admin_site.admin_view(
                    PrintSemesterSchedule.as_view(
                        template_name="classes/print/semester_schedule_enrollment.tex"
                    )
                ),
                name="classes-semester-print-enrollment",
            ),
        ] + urls
        return urls

    def print_semester_schedule(self, request, queryset):
        """
        Redirect to the actual view.
        """
        url = reverse_lazy("admin:classes-semester-print-schedule")
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        query = "&".join(["pk={0}".format(s) for s in selected])
        return HttpResponseRedirect(url + "?" + query)

    print_semester_schedule.short_description = (
        "Generate PDF schedule for selected semesters"
    )

    def print_semester_enrollment(self, request, queryset):
        """
        Redirect to the actual view.
        """
        url = reverse_lazy("admin:classes-semester-print-enrollment")
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        query = "&".join(["pk={0}".format(s) for s in selected])
        return HttpResponseRedirect(url + "?" + query)

    print_semester_enrollment.short_description = (
        "Generate PDF schedule with enrollment"
    )

    def spreadsheet_semester_enrollment(self, request, queryset):
        """
        Redirect to the actual view.
        """
        url = reverse_lazy("admin_export_spreadsheet")
        # this query is for the corresponding PKs of SectionSchedules
        pk_list = (
            SectionSchedule.objects.filter(
                section__term__in=queryset, section__course__department__advertised=True
            )
            .active()
            .values_list("pk", flat=True)
            .distinct()
        )
        query = "&".join(["pk={0}".format(s) for s in pk_list])
        query += "&format=xlsx"
        ct = ContentType.objects.get_for_model(SectionSchedule)
        query += "&contenttype={0}".format(ct.pk)
        return HttpResponseRedirect(url + "?" + query)

    spreadsheet_semester_enrollment.short_description = (
        "Generate XLSX schedule with enrollment"
    )


admin.site.register(Semester, SemesterAdmin)

##############################################################


class TimeslotAdmin(admin.ModelAdmin):
    actions = [mark_active, mark_inactive, mark_scheduled]
    list_display = ["name", "day", "start_time", "stop_time", "scheduled"]
    list_filter = ["active", "scheduled"]
    search_fields = ["name"]


admin.site.register(Timeslot, TimeslotAdmin)

##############################################################


class CourseHandoutAdmin(admin.ModelAdmin):

    autocomplete_fields = ["course"]
    actions = [mark_active, mark_inactive]
    form = CourseHandoutForm
    list_display = ["course", "label", "ordering", "path"]
    list_filter = ["label"]
    ordering = ["course", "ordering", "label"]
    # raw_id_fields = ['course', ]


admin.site.register(CourseHandout, CourseHandoutAdmin)

##############################################################


class SectionHandoutAdmin(admin.ModelAdmin):
    def section_display_list(self, obj):
        return "{0} {1}".format(obj.section.course.label, obj.section.section_name)

    section_display_list.short_description = "section"

    def section_term_list(self, obj):
        return "{}".format(obj.section.term)

    section_term_list.short_description = "term"

    actions = [mark_active, mark_inactive]
    form = SectionHandoutForm
    list_display = [
        "section_display_list",
        "section_term_list",
        "label",
        "ordering",
        "path",
    ]
    list_filter = ["label", SectionSemesterFilter, SectionCourseFilter]
    ordering = ["-section__term", "section", "label"]
    raw_id_fields = ["section"]


admin.site.register(SectionHandout, SectionHandoutAdmin)

##############################################################


class ImportantDateAdmin(admin.ModelAdmin):
    actions = [mark_active, mark_inactive]
    list_display = ["date", "title", "end_date", "no_class", "university_closed"]
    list_filter = ["active", "no_class", "university_closed"]
    ordering = ["-date"]


admin.site.register(ImportantDate, ImportantDateAdmin)

##############################################################


@admin.register(Requisite)
class RequisiteAdmin(admin.ModelAdmin):
    autocomplete_fields = ["course"]
    list_display = ["__str__", "rank"]
    list_filter = ["active", "rank"]
    search_fields = [
        "course__department__code",
        "course__department__name",
        "course__code",
        "outside_course",
    ]

    def view_on_site(self, obj):
        """
        Provide this because sometimes the object
        doesn't have a site url.
        """
        return obj.get_absolute_url()


##############################################################

admin.site.register(SemesterDateRange)

##############################################################
##############################################################
##############################################################
