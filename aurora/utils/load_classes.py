# -*- encoding: utf-8
#
# This module converts aurora records (from .aurora_scrape)
# into usuable objects.
#
#######################
from __future__ import print_function, unicode_literals

from pprint import pprint

from classes.models import (
    Course,
    Department,
    ScheduleType,
    Section,
    SectionSchedule,
    Semester,
    Timeslot,
)
from django.template.defaultfilters import slugify
from django.utils.encoding import force_text
from people.models import EmailAddress, Person
from places.models import ClassRoom

from .. import conf
from ..models import (
    AuroraCampus,
    AuroraDateRange,
    AuroraDepartment,
    AuroraInstructor,
    AuroraLocation,
    AuroraTimeslot,
)
from .aurora_scrape import fetch_catalog_entry

#######################


def check_record(record, verbosity):
    """
    Returns a boolean indicated whether or not this record should be processed.
    """
    if "campus" not in record:
        if conf.get("banner:accept_no_campus"):
            return True
        else:
            if verbosity > 1:
                print("[!] rejecting record -- no campus")
            return False

    if AuroraCampus.objects.is_blacklisted(record["campus"]):
        if verbosity > 1:
            print("[!] rejecting course record -- AuroraCampus is Blacklisted.")
        return False
    if not record["class_section"]:
        if verbosity > 1:
            print("[!] rejecting course record -- no class_section")
        return False

    return True


_course_desc_cache = None


def load_course(record):
    """
    Load a course object from the aurora_scrape record.
    Returns the course and a list of warnings associated with the load.

    This function creates a course if it doesn't exist.
    """
    global _course_desc_cache

    warnings = []
    course_name = record["class_name"]
    if " " not in course_name:
        pprint(record)
        return None, ["Malformed course record.  Ignoring."]  # malformed record.
    dept_code, course_code = course_name.split(None, 1)
    department, created = AuroraDepartment.objects.find(dept_code, create=False)
    course_verbose_name = record["class_verbosename"]
    course, created_flag = Course.objects.get_or_create(
        department=department,
        code=course_code,
        defaults={"name": course_verbose_name, "slug": slugify(course_name)},
    )
    if created_flag:
        warnings.append("Course record created")

    if course.pk not in _course_desc_cache:
        if not course.description and "catalog_entry_href" in record:
            desc = fetch_catalog_entry(record["catalog_entry_href"])
            if course.description != desc:
                course.description = desc
                course.save()
                warnings.append("Updated course description")
        _course_desc_cache[course.pk] = True  # mark done

    # Do NOT reactivate courses.  If they are deactivated, they are deactivated
    #   for a reason!
    return course, warnings


def load_term(record):
    """
    Load a Semester object from the aurora_scrape record.

    This function creates a term (and mapping) if it does not exist.
    """
    warnings = []
    associated_term = record["associated_term"]

    semester = Semester.objects.get_by_name(associated_term)
    # print(repr(associated_term), semester)
    assert semester is not None, "semester should never be None"
    return semester, warnings


def load_term_date_range(schedule, verbosity):
    """
    Load a date_range object.
    """
    warnings = []
    if schedule is None or "date_range" not in schedule:
        return None, warnings
    schedule_date_range = schedule["date_range"]
    if verbosity > 2:
        print("schedule_date_range =", schedule_date_range)
    date_range, created = AuroraDateRange.objects.find(schedule_date_range, create=True)
    if created:
        warnings.append("Created semester date range: " + "{}".format(date_range))
    # print(repr(schedule_date_range), date_range)
    return date_range, warnings


def load_instructors(record, verbosity):
    """
    Load an Instructor object from the aurora_scrape record.

    This function does *not* create a new object, unless the config setting
    'create_instructors' is True.

    Note that, since there can be multiple instructors; this function
    always operates on lists.
    The primary instructor is always first in the returned list.
    """
    warnings = []
    primary = record.get("instructor_primary", None)
    name_list = record.get("instructors", [])
    if primary is not None:
        name_list.insert(0, primary)

    name_list = [force_text(name) for name in name_list]
    email_map = record.get("instructors_email", {})

    def _do_single(name):
        email_addr = email_map.get(name, None)
        if verbosity > 2:
            print(
                "- instructor search:: name = {0!r}; email_addr = {1!r}".format(
                    name, email_addr
                )
            )
        instructor, created = AuroraInstructor.objects.find(
            name, email_addr, create=conf.get("create_instructors")
        )
        if created:
            warnings.append(
                "New person object created for instructor role: {0}".format(name)
            )
        return instructor

    instructor_list = [_do_single(name) for name in name_list]
    return instructor_list, warnings


def load_timeslot(schedule, verbosity):
    """
    Load an Timeslot object from the aurora_scrape record.

    This function does *not* create a new object.
    """
    warnings = []
    if "days" not in schedule or "time" not in schedule:
        return Timeslot.objects.TBA(), []
    days = schedule["days"]
    time = schedule["time"]
    timeslot, created = AuroraTimeslot.objects.find(
        days, time, create=conf.get("create_timeslots")
    )
    if not timeslot:
        warnings.append("Could not find timeslot: " + days + " @ " + time)
        timeslot = Timeslot.objects.TBA()
    if created:
        warnings.append("New timeslot object created for: {0} @ {1}".format(days, time))
    return timeslot, warnings


def load_room(schedule, verbosity):
    """
    Load an ClassRoom object from the aurora_scrape record.

    This function does *not* create a new object, unless the _CONFIG
    setting 'create_classrooms' is True.
    """
    warnings = []
    where = schedule.get("where", None)
    if where is None:
        return ClassRoom.objects.TBA(), []
    try:
        room, created = AuroraLocation.objects.find(
            where, create=conf.get("create_classrooms")
        )
    except AssertionError as e:
        warnings.append("{}".format(e))
        room = None
        created = False

    if room is None:
        warnings.append("Could not find location: " + where)
        room = ClassRoom.objects.TBA()
    elif created:
        warnings.append("Created classroom object for location: {0}".format(where))

    return room, warnings


def load_schedule_type(schedule, verbosity):
    """
    Load a ScheduleType from the record.

    This function **does** create new objects.
    """
    warnings = []
    if "type" not in schedule:
        warnings.append("No schedule type specified")
        # The name is '(none)'
        # because schedule_type cannot be None.
        name = "(none)"
    else:
        name = schedule["type"]
    obj, created = ScheduleType.objects.get_or_create(name=name)
    if created:
        warnings.append("Created new schedule type: %r" % name)
    return obj, warnings


def load_schedule(section, record, warnings, verbosity):
    """
    Load the SectionSchedule
    """
    if "schedule" not in record:
        return

    source_list = []
    for sched_rec in record["schedule"]:
        # pprint(sched_rec)
        data = {}
        data["section"] = section
        for data_name, verbose_name, load_function in (
            ("date_range", "Date range", load_term_date_range),
            ("timeslot", "Timeslot", load_timeslot),
            ("room", "Room", load_room),
            ("type", "Schedule type", load_schedule_type),
            ("instructors", "Instructor", load_instructors),
        ):
            data[data_name], subwarnings = load_function(sched_rec, verbosity)
            for warning in subwarnings:
                warnings.append(verbose_name + ": " + warning)

        # rooms and timeslots can change
        # uniquely key on section, type, date_range combo.

        instructors = data.pop("instructors")
        primary_instructor = instructors[0] if instructors else None
        data["instructor"] = primary_instructor
        additional_instructors = instructors[1:]
        sched, created = SectionSchedule.objects.get_or_create(
            section=data["section"],
            type=data["type"],
            date_range=data["date_range"],
            timeslot=data["timeslot"],
            defaults=data,
        )

        if sched.room != data["room"] and not sched.override_room:
            sched.room = data["room"]
            warnings.append("Schedule: Updated room to %s" % sched.room)
            sched.save()

        if sched.instructor != primary_instructor and not sched.override_instructor:
            sched.instructor = primary_instructor
            warnings.append(
                "Schedule: Updated instructor to {sched.instructor}".format(sched=sched)
            )
            sched.save()
        # TODO: multiple instructors
        if (
            set(sched.additional_instructors.all()) != set(additional_instructors)
            and not sched.override_instructor
        ):
            sched.additional_instructors.set(additional_instructors)
            if additional_instructors:
                l = [str(p) for p in additional_instructors]
                s = ", ".join(l) if l else "---"
                warnings.append(
                    "Schedule: Updated additional instructors to {}".format(s)
                )
            else:
                warnings.append("Schedule: Cleared additional instructors")

        if sched.timeslot != data["timeslot"]:
            sched.timeslot = data["timeslot"]
            warnings.append("Schedule: Updated timeslot to %s" % sched.timeslot)
            sched.save()

        if not sched.active:
            sched.active = True
            sched.save()

        source_list.append(sched.pk)

    # now we also need to go through a second time for things that are in the
    # database but are no longer in banner/aurora.

    for sched in SectionSchedule.objects.filter(section=section):
        if sched.pk not in source_list:
            if sched.active:
                sched.active = False
                sched.save()
                warnings.append(
                    "Schedule: Deactivated {0} (no longer valid)".format(sched)
                )


def load_section(record, term, verbosity):
    """
    Convert a top level record from aurora_scrape into a section object.

    Return the section object, and a list of warnings from the conversion.
    """
    warnings = []
    data = {}
    data["active"] = True  # or True, if term is current...
    course, subwarnings = load_course(record)
    for warning in subwarnings:
        warnings.append("{}".format(course) + ": " + warning)
    if course is None:
        return None, warnings

    section_name = record["class_section"]
    data["crn"] = record["class_crn"]

    instructors, subwarnings = load_instructors(record, verbosity)
    data["instructor"] = instructors[0] if instructors else None
    additional_instructors = instructors[1:]
    for warning in subwarnings:
        warnings.append("Instructor: " + warning)

    data["slug"] = slugify(course.slug + " " + section_name + " " + term.slug)

    section, created_flag = Section.objects.get_or_create(
        course=course, section_name=section_name, term=term, defaults=data
    )
    if created_flag:
        warnings.append("Section object created")
    else:
        for key, value in data.items():
            if key == "instructor":
                continue
            if getattr(section, key) != value:
                setattr(section, key, value)
                warnings.append(key + ": value updated -> " + "{}".format(value))
            section.save()

        if section.instructor != data["instructor"] and not section.override_instructor:
            if data["instructor"] is not None:
                section.instructor = data["instructor"]
                warnings.append("Updated instructor to %s" % section.instructor)
                section.save()

    if (
        set(section.additional_instructors.all()) != set(additional_instructors)
        and not section.override_instructor
    ):
        if additional_instructors:
            # instructors may have been promoted by instructor_beat
            section.additional_instructors.set(additional_instructors)
            if additional_instructors:
                l = [str(p) for p in additional_instructors]
                s = ", ".join(l) if l else "---"
                warnings.append("Updated additional instructors to {}".format(s))
            else:
                warnings.append("Cleared additional instructors")

    load_schedule(section, record, warnings, verbosity)

    return section, warnings


def load_classes(year, term, dept_code, record_list, delete=False, verbosity=0):
    """
    Load the data from aurora_scrape.  Return a dictionary of warnings.
    """
    global _course_desc_cache
    _course_desc_cache = {}  # reset descriptions
    results = {}

    # print('load_classes(year={year!r}, term={term!r}, ...)')

    semester = Semester.objects.get_by_pair(year, term)
    aurora_list = []
    for course_record in record_list:
        if not check_record(course_record, verbosity):
            continue
        section, warnings = load_section(course_record, semester, verbosity)
        if verbosity > 1:
            print("Loaded section {}".format(section))
        results[section] = warnings
        aurora_list.append(section)
    # now go through and remove local entries no longer in aurora.
    if delete:
        for old_section in Section.objects.filter(
            course__department__code=dept_code, term=semester
        ):
            if (old_section not in aurora_list) and (
                old_section.section_type not in conf.get("delete:ignore_section_types")
            ):
                results["{}".format(old_section)] = [
                    "DELETE section no longer available"
                ]
                old_section.delete()

    return results


#####
