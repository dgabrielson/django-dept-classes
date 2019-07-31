"""
Generate the schedule of courses.
"""
#######################
from __future__ import print_function, unicode_literals

from ..models import Section, Semester

#######################

DJANGO_COMMAND = "main"
OPTION_LIST = ()
HELP_TEXT = __doc__.strip()


def get_course_display(course, schedule):
    result = course.label
    sched_type = "{}".format(schedule.type)
    if sched_type == "Lecture":
        pass
    elif sched_type in ["Lab", "Laboratory", "Tutorial"]:
        result += "#"
    else:
        result += " (" + sched_type + ")"
    return result


def get_timeslot_display(timeslot):
    label = timeslot.label()
    if label == "None":
        return ""
    if label.startswith("Slot "):
        return label
    else:
        # if label.startswith('Time '):
        return (
            timeslot.get_start_time_display() + " - " + timeslot.get_stop_time_display()
        )
    # return label + ': ' + timeslot.get_start_time_display() + ' - ' + timeslot.get_stop_time_display()


def get_timeslot_days_display(timeslot):
    if timeslot.label() == "None":
        return ""
    return timeslot.get_day_display()


def get_instructor_display(section):
    if section.instructor is not None:
        return "{}".format(instructor)

    return "TBA"


def get_room_display(room):
    return "{}".format(room)


def do_section_schedule(course, section, schedule):
    """
    Generate for a single scheduling of a section.
    """
    result = []
    result.append(get_course_display(course, schedule))
    result.append(section.term.get_term_display())
    result.append(section.crn)
    result.append(section.section_name)
    result.append(get_timeslot_display(schedule.timeslot))
    result.append(get_instructor_display(section))
    result.append(get_timeslot_days_display(schedule.timeslot))
    result.append(get_room_display(schedule.room))
    return result


def do_section(course, section):
    """
    Generate for a single section
    """
    result = []
    for sched in section.sectionschedule_set.active():
        result.append(do_section_schedule(course, section, sched))
    return result


def do_term(term):
    """
    Generate for a single term
    """
    result = []
    for course in term.course_list:
        for section in course.section_set.all().filter(term=term):
            result.extend(do_section(course, section))
    return result


def generate_data_table():
    """
    Build the data.
    """
    result = []
    term_list = Semester.objects.advertised()
    for term in term_list:
        if term.term != "2":  # no summer!
            result.extend(do_term(term))
    return result


def save_data(table):
    """
    For now, dump to standard out in a tab format table.
    """
    for row in table:
        print("\t".join(row))


def main(options, args):
    """
    Do it. 
    """
    data = generate_data_table()
    save_data(data)
