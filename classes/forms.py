# -*- coding: utf-8 -*-
#######################
from __future__ import print_function, unicode_literals

from django import forms
from django.db.models.query import QuerySet
from django.db.utils import ProgrammingError
from django.forms import widgets

from . import conf
from .models import Course, CourseHandout, Section, SectionHandout, Semester
from .utils import unique_courses

#######################
##############################################################

##############################################################


class CourseSectionInputWidget(widgets.Input):
    """
    Activate in a form by specifying a field such as:
    Course_Section = forms.ModelChoiceField(
                            Section.objects.active(),
                            label='Course & Section',
                            widget = CourseSectionInputWidget(
                                        Section.objects.active(),
                                        on_section_change="document.getElementById('section-select-form').submit()",
                                        )
                            )

    Or, for more dynamic forms, activate by (in your view):
    CourseSelectForm.base_fields['Course_Section'].widget = CourseSectionInputWidget(sections,
                                                                on_section_change= "document.getElementById('section-select-form').submit()")
    form = CourseSelectForm(initial={'Course_Section': request.session['section_id']})


    NOTE: on_section_change is javascript which may be called in two different ways:
        (1) when the section pull down is changed; OR
        (2) when a course with only one section is selected.
    The most effective way to do this is demonstrated above: give your form an id
        (id="section-select-form" in this case) and access the form via the DOM.
        DO NOT ACCESS THE FORM VIA this.form.submit() --- it will NOT WORK!

    """

    class Media:
        css = {"all": ("classes/css/sectionselect.css",)}

    def __init__(self, sections, preselected_id=None, on_section_change=None):
        widgets.Widget.__init__(self)
        self.preselected_id = preselected_id
        self.on_section_change = on_section_change
        self.load_sections(sections)

    def load_sections(self, sections):
        if isinstance(sections, list):
            # remove duplications by sorting a set
            self.sections = sorted(
                set(sections), key=lambda e: (e.course.label, e.section_name)
            )
        elif isinstance(sections, QuerySet):
            # remove duplicates via distinct
            self.sections = sections.distinct()
        else:
            self.sections = sections
        self.sections = sections
        self.course_map = {}
        self.courses = unique_courses(self.sections)
        self.in_between_html = "&nbsp;&nbsp;"
        for course in self.courses:
            self.course_map[course.id] = [
                section.id
                for section in self.sections
                if section.course.pk == course.pk
            ]

    def __get_section_by_id(self, section_id):
        for section in self.sections:
            if section.pk == section_id:
                return section
        return None

    def render(self, name, value, attrs=None):
        """
        This should do a better job of respect ``attrs``.
        """
        # Debugging render:
        # assert False, 'stop here'
        debug_str = ""
        # import pprint
        # debug_str = u'<pre>name = ' + "{}".format(repr(name)) + u'\nvalue = ' + "{}".format(repr(value)) + u'\nattrs = ' + "{}".format(repr(attrs)) + u'\n' + "{}".format(pprint.pformat(self.course_map, width=60)) + u'</pre>'

        if "id" in attrs:
            html_id = attrs["id"]
        else:
            html_id = name + "_id"

        try:
            selected_section_id = int(value)  # this is a PK/ID.
        except (ValueError, TypeError):
            selected_section_id = None
        # validate that this ID is one of the options, otherwise ignore it:
        selected_course_id = None
        for course in self.courses:
            if (
                selected_section_id in self.course_map[course.pk]
                or len(self.courses) == 1
            ):
                selected_course_id = course.pk
        if selected_course_id is None:
            selected_section_id = None

        # setup javascript
        javascript = (
            """<script type="text/javascript">
function %s_change(course_obj_id, section_obj_id)
{
    course_obj = document.getElementById(course_obj_id);
    selected_course_index = course_obj.selectedIndex;
    selected_course_id = -1;
    for (var i = 0; i < course_obj.options.length; i++) {
        if (course_obj.options[i].selected == true) {
            selected_course_id = course_obj.options[i].value;
            break
        }
    }
    section_obj = document.getElementById(section_obj_id);
"""
            % html_id
        )
        for course_id, section_id_list in self.course_map.items():
            javascript += "    if (selected_course_id == %d) {\n" % course_id
            # javascript += u'        alert("JavaScript, course change to id %d; new length of options = %d");' % (course_id, len(section_id_list) )
            javascript += "        section_obj.options.length = 0;\n"
            if len(section_id_list) > 1:
                javascript += '        section_obj.options[section_obj.options.length] = new Option("--", null, true, true);\n'
            for section_id in section_id_list:
                section = self.__get_section_by_id(section_id)
                if len(section_id_list) == 1:
                    selected = "true"
                else:
                    selected = "false"
                javascript += (
                    '        section_obj.options[section_obj.options.length] = new Option("%s", "%d", %s, %s);\n'
                    % (section.section_name, section.pk, selected, selected)
                )
            if len(section_id_list) == 1 and self.on_section_change is not None:
                javascript += "        " + self.on_section_change + ";\n"
            javascript += "    }\n"
        javascript += """}
</script>"""

        # setup html for course selector
        selected_course_id = -1  # TODO: clean this up
        course_html = (
            '<select id="%s_course" class="sectionselectcourse" onChange="%s_change(\'%s_course\', \'%s\')">'
            % (html_id, html_id, html_id, html_id)
        )
        if selected_section_id is None:
            if len(self.courses) > 1:
                course_html += "<option selected>-- Choose a course --</option>"
        for course in self.courses:
            selected = (
                selected_section_id in self.course_map[course.pk]
                or len(self.courses) == 1
            )
            selected_html = ""
            if selected:
                selected_html = " selected"
                selected_course_id = course.id
            course_html += '<option class="courseoption" value="%d"%s>%s</option>' % (
                course.id,
                selected_html,
                str(course),
            )
        course_html += "</select>"

        # setup html for section selector
        if self.on_section_change is None:
            section_html = '<select name="%s" id="%s" class="sectionselect">' % (
                name,
                html_id,
            )
        else:
            section_html = (
                '<select name="%s" id="%s" class="sectionselect" onChange="%s">'
                % (name, html_id, self.on_section_change)
            )

        if selected_section_id is None or selected_course_id == -1:
            section_html += "<option>--</option>"
        if selected_course_id != -1:
            # assert False, 'selected_section_id = %r render()' % selected_section_id
            for section_id in self.course_map[selected_course_id]:
                section = self.__get_section_by_id(section_id)
                selected_html = ""
                if section.pk == selected_section_id:
                    selected_html = " selected"
                section_html += '<option value="%d"%s>%s</option>' % (
                    section.pk,
                    selected_html,
                    section.section_name,
                )

        section_html += "</select>"

        return (
            debug_str + javascript + course_html + self.in_between_html + section_html
        )


##############################################################


class MultiSectionFilterHelpersMixin(object):
    def _remove_sectiontype_bad_codes(self, qs_codes):
        for code in ["00", "zz"]:
            if code in qs_codes:
                # do not honour the unknown/other code
                qs_codes.remove(code)
        return qs_codes

    def _get_sectiontype_choices(self, queryset):
        try:
            qs_codes = set(queryset.values_list("section_type", flat=True))
        except ProgrammingError as e:
            # happens when db does not yet exist.
            return []
        qs_codes = self._remove_sectiontype_bad_codes(qs_codes)
        choices = conf.get("section_type:choices")
        for code, label in choices:
            if code in qs_codes:
                yield (code, label)


##############################################################


class InnerCheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
    template_name = "classes/forms/widgets/innercheckboxselectmultiple.html"


class MultiSectionFilterWidget(MultiSectionFilterHelpersMixin, widgets.MultiWidget):
    """
    A MultiWidget widget for filtering sections to a queryset.
    https://docs.djangoproject.com/en/1.11/ref/forms/widgets/
    Section filtering is split by course, term, and a list of checkboxes
    for section type.
    """

    def _get_course_choices(self, queryset):
        vl = queryset.values_list(
            "course_id", "course__department__code", "course__code"
        )
        try:
            return sorted(
                list(set(((id, dept + " " + course) for id, dept, course in vl))),
                key=lambda e: e[1],
            )
        except ProgrammingError as e:
            # happens when db does not yet exist.
            return []

    def _get_semester_choices(self, queryset):
        qs = (
            Semester.objects.filter(pk__in=queryset.values_list("term_id", flat=True))
            .distinct()
            .reverse()
        )
        try:
            for o in qs:
                yield (o.pk, str(o))
        except ProgrammingError as e:
            # happens when db does not yet exist.
            return []

    def __init__(self, queryset, attrs=None):
        text_attrs = attrs.copy() if attrs is not None else {}
        if "max_length" not in text_attrs:
            text_attrs["max_length"] = 4
        if "size" not in text_attrs:
            text_attrs["size"] = 4
        if "placeholder not in text_attrs":
            text_attrs["placeholder"] = "all"
        _widgets = [
            widgets.Select(attrs, choices=self._get_course_choices(queryset)),
            widgets.Select(attrs, choices=self._get_semester_choices(queryset)),
            widgets.TextInput(text_attrs),
            InnerCheckboxSelectMultiple(
                attrs, choices=self._get_sectiontype_choices(queryset)
            ),
        ]
        return super(MultiSectionFilterWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        """
        From the docs:
        This method takes a single “compressed” value from the field and
        returns a list of “decompressed” values. The input value can be
        assumed valid, but not necessarily non-empty.

        In practices, this seems to be a list of pk values or a single
        pk value depending on the initial value.

        Assume ``value`` is a Section queryset.
        """

        def _course():
            s = set(value.values_list("course_id", flat=True))
            if len(s) == 1:
                return s.pop()

        def _semester():
            s = set(value.values_list("term_id", flat=True))
            if len(s) == 1:
                return s.pop()

        def _section_name():
            s = set(value.values_list("section_name", flat=True))
            if len(s) == 1:
                return s.pop()

        def _section_types():
            s = set(value.values_list("section_type", flat=True))
            return list(self._remove_sectiontype_bad_codes(s))

        if value:
            result = [_course(), _semester(), _section_name(), _section_types()]
            return result
        return [None, None, None, None]


##############################################################


class MultiSectionFilterField(MultiSectionFilterHelpersMixin, forms.MultiValueField):
    """
    A MultiValueField field for filtering sections for a selection.
    Uses the ``MultiSectionFilterWidget`` by default.
    """

    def __init__(self, *args, **kwargs):
        if "queryset" not in kwargs:
            kwargs["queryset"] = Section.objects.active().advertised()
        self.queryset = kwargs.pop("queryset")

        fields = (
            forms.ModelChoiceField(
                queryset=Course.objects.filter(
                    pk__in=self.queryset.values_list("course_id", flat=True)
                ).distinct(),
                error_messages={"incomplete": "Select a course"},
            ),
            forms.ModelChoiceField(
                queryset=Semester.objects.filter(
                    pk__in=self.queryset.values_list("term_id", flat=True)
                ).distinct(),
                error_messages={"incomplete": "Select a term"},
            ),
            forms.CharField(max_length=4, required=False),
            forms.MultipleChoiceField(
                choices=self._get_sectiontype_choices(self.queryset), required=False
            ),
        )
        if "widget" not in kwargs:
            kwargs["widget"] = MultiSectionFilterWidget(self.queryset)
        if "initial" not in kwargs:
            course_slug = conf.get("multisectionfilterfield:default-course-slug")
            if course_slug is not None:
                try:
                    self.initial = Section.objects.advertised().filter(
                        term=Semester.objects.get_current(), course__slug=course_slug
                    )
                except ProgrammingError as e:
                    # database does not yet exist
                    pass
                else:
                    kwargs["initial"] = self.initial
        if "help_text" not in kwargs:
            kwargs[
                "help_text"
            ] = "Select course and term; optionally specify one section or select the types of sections"
        kwargs["fields"] = fields
        kwargs["require_all_fields"] = False
        return super(MultiSectionFilterField, self).__init__(*args, **kwargs)

    def compress(self, value_list):
        course, term, section_name, section_types = value_list
        qs = Section.objects.filter(course=course, term=term)
        if section_name:
            qs = qs.filter(section_name__iexact=section_name)
        if section_types:
            qs = qs.filter(section_type__in=section_types)
        if not section_name and not section_types:
            raise forms.ValidationError(
                "Either specify a section name, or one or more section types"
            )
        if not qs.exists() and self.required:
            raise forms.ValidationError("No matching sections found")
        return qs


##############################################################


class CourseHandoutForm(forms.ModelForm):
    """
    Form for course outlines.
    """

    class Meta:
        model = CourseHandout
        fields = ["course", "label", "ordering", "public", "path"]


##############################################################


class SectionHandoutForm(forms.ModelForm):
    """
    Form for course outlines.
    """

    class Meta:
        model = SectionHandout
        fields = ["section", "label", "ordering", "path"]


##############################################################
