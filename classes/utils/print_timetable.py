"""
Utilities for generating a printable timetable of classes.
"""
###############################################################
#######################
from __future__ import print_function, unicode_literals

import datetime
from itertools import chain, groupby

from classes.models import SectionSchedule, Semester
from django.template.loader import render_to_string
from people.models import Person

#######################

###############################################################


def preliminary_table(schedule_list):
    # construct preliminary timetable
    timetable = {}
    for timeslot, items in groupby(schedule_list, lambda e: e.timeslot):
        litems = list(items)
        for day in timeslot.day:
            if day not in "MTWRF":
                continue
            if day not in timetable:
                timetable[day] = {}
            if timeslot.start_time not in timetable[day]:
                timetable[day][timeslot.start_time] = []
            timetable[day][timeslot.start_time] += litems
    return timetable


###############################################################


def _instructor_abbrev_map(schedule_list):
    # map instructors to name abbreviations

    def auto_abbreviate(name, n=1):
        if name is None:
            return ""
        parts = name.split()
        first_parts = "".join([p[0] for p in parts[:-1]])
        last_part = parts[-1][:n]
        return first_parts + last_part

    instr_pks = set(
        schedule_list.exclude(instructor__isnull=True).values_list(
            "instructor_id", flat=True
        )
    )
    instr_pks.update(
        schedule_list.exclude(additional_instructors__isnull=True).values_list(
            "additional_instructors", flat=True
        )
    )
    instructor_qs = Person.objects.filter(pk__in=instr_pks).distinct()

    name_map = {}
    collision_map = {}
    instr_map = {}
    for instr in instructor_qs:
        instr_map[instr.pk] = instr
        abbr = instr.personkeyvalue_set.lookup("initials")
        if abbr is None:
            abbr = auto_abbreviate(instr.cn, 1)
            collision_map[instr.pk] = True
        else:
            abbr = abbr.value
            collision_map[instr.pk] = None
        name_map[instr.pk] = abbr

    # collision check...
    def _collision_check(name_map, collision_map):
        value_list = list(name_map.values())
        for key, value in name_map.items():
            count = value_list.count(value)
            if count == 1:
                collision_map[key] = None
            else:
                collision_map[key] = [k for k, v in name_map.items() if v == value]

    _collision_check(name_map, collision_map)

    # first fix: auto_abbreviate(..., 2)
    for key, value in collision_map.items():
        if value is not None:
            for pk in value:
                instr = instr_map[pk]
                name_map[pk] = auto_abbreviate(instr.cn, 2)

    _collision_check(name_map, collision_map)

    # second fix: numbers.
    key_done = []
    for key, value in collision_map.items():
        if key in key_done:
            continue
        if value is not None:
            n = 1
            for count, pk in enumerate(value, 1):
                name_map[pk] += "{}".format(count)
                key_done.append(pk)

    # final check: there should be no collisions here...
    _collision_check(name_map, collision_map)
    assert not any([v for k, v in collision_map.items()]), "still have collisions"
    return name_map


###############################################################


def _format_multisection(schedule, name_map, schedule_list):
    result = schedule.section.course.code
    if schedule.type.name not in ["Lecture", "Class"]:
        result += " " + schedule.type.name[:3]
    if (
        len(
            set(
                schedule_list.filter(
                    section__course=schedule.section.course
                ).values_list("section__section_name", flat=True)
            )
        )
        > 1
    ):
        result += " " + schedule.section.section_name
    abbrev = name_map.get(schedule.instructor_id, None)
    if abbrev:
        result += ": " + abbrev
    return result


###############################################################


def _collapse_timeslot(schedule_list, name_map, schedule_qs):
    results = []
    seen = set()
    # collapse cross numbered courses -- same location, same instructor
    xlist_map = {}
    for sched in schedule_list:
        if sched.instructor_id is None:
            continue
        key = sched.instructor_id, sched.room_id
        if key in xlist_map:
            # assume cross listed courses are never multisection...
            results.append(
                "{1}/{2}: {3}".format(
                    xlist_map[key].section.course.department.code,
                    xlist_map[key].section.course.code,
                    sched.section.course.code,
                    name_map[sched.instructor_id],
                )
            )
            seen.add(xlist_map[key])
            seen.add(sched)
        else:
            xlist_map[key] = sched
    # collapse section names -- if there is more than one section, keep section_name; else just course name
    for sched in schedule_list:
        if sched in seen:
            continue
        results.append(_format_multisection(sched, name_map, schedule_qs))
        seen.add(sched)
    return sorted(results)


###############################################################


def _initial_display_table(timetable, name_map, schedule_list):
    # construct display timetable:
    display_timetable = {}
    for day in timetable:
        display_timetable[day] = {}
        for time in timetable[day]:
            display_timetable[day][time] = _collapse_timeslot(
                timetable[day][time], name_map, schedule_list
            )
    return display_timetable


###############################################################


def latex_time_formatter(t):
    return "\\cellformat{{{0}}}".format(t.strftime("%H:%M").lstrip("0"))


def _display_timetable(timetable, time_formatter=None):
    # display timetable is column oriented (column major order);
    # need to convert to LaTeX/tabular (row major order).
    M = 0

    # make sure we have at least the five weekdays in the timetable:
    for day in "MTWRF":
        i = 0
        if day not in timetable:
            timetable[day] = {}

    # construct strictly ordered sequence of times; ``timetable[day]``
    times = sorted(list(set(sum([list(timetable[day]) for day in timetable], []))))
    t_idx_map = {t: i for i, t in enumerate(times)}

    # grid max determines the maximum number of lines for each time.
    grid_max = {}
    for t in times:
        grid_max[t] = max((len(timetable.get(d, {}).get(t, [])) for d in timetable))

    # determine actual index of each time over all days.
    for idx, t in enumerate(times):
        # does the next time occur on any of the same days as this time?
        next_time = times[idx + 1] if idx + 1 < len(times) else None
        if next_time is not None:
            t_idx_map[next_time] = max([t_idx_map[t] + grid_max[t], t_idx_map[t]]) + 1

    # make spots for worst case layout all times every day:
    day_length = {}
    for day in timetable:
        daytimes = sorted(list(timetable[day]))
        last_time = daytimes[-1]
        day_length[day] = t_idx_map[last_time] + len(timetable[day][last_time])

    M = max(day_length.values()) + 1

    tabular = []
    for day in "MTWRF":
        tabular.append([])
        for i in range(M):
            tabular[-1].append("")
        i = 0
        for t in sorted(timetable[day].keys()):
            # pad to time_idx
            i = t_idx_map[t]
            tabular[-1][i] = time_formatter(t) if time_formatter is not None else t
            i += 1
            for course in timetable[day][t]:
                tabular[-1][i] = course
                i += 1

    tabular_t = []
    for j in range(M):
        tabular_t.append([])
        for i in range(5):
            tabular_t[-1].append(tabular[i][j])

    return tabular_t


###############################################################


def timetable(semester, time_formatter=None, schedule_types=None):
    """
    Generate the timetable for a semester.
    Lots of assumptions here....
    """
    if schedule_types is None:
        schedule_types = ["Lecture", "Tutorial", "Laboratory", "Session"]
    schedule_list = SectionSchedule.objects.active().filter(
        section__term=semester,
        section__course__department__advertised=True,
        type__name__in=schedule_types,
    )
    t1 = preliminary_table(schedule_list)
    name_map = _instructor_abbrev_map(schedule_list)
    t2 = _initial_display_table(t1, name_map, schedule_list)
    t3 = _display_timetable(t2, time_formatter=time_formatter)
    return t3


###############################################################


def latex_tabular_list(semester, schedule_types=None):
    return timetable(
        semester, time_formatter=latex_time_formatter, schedule_types=schedule_types
    )


###############################################################
