"""
Load timeslot information.

Typically, this would be run through a filter such as:
 ./django aurora load_classes | grep Could.not.find.timeslot | sort | uniq | cut -f 3- -d : | ./django classes make_timeslots
"""
#######################
from __future__ import print_function, unicode_literals

import sys
from datetime import datetime

from classes.models import Timeslot

#######################

DJANGO_COMMAND = "main"
OPTION_LIST = ()
HELP_TEXT = __doc__.strip()

AURORA_TIME_FMT = "%I:%M %p"


def read_times(schedule_time):
    start_time_str, finish_time_str = [e.strip() for e in schedule_time.split("-", 1)]
    start_dt = datetime.strptime(start_time_str, AURORA_TIME_FMT)
    finish_dt = datetime.strptime(finish_time_str, AURORA_TIME_FMT)
    return start_dt.time(), finish_dt.time()


def main(options, args):
    text = sys.stdin.read().strip()
    lines = [e.strip() for e in text.split("\n")]

    for line in lines:
        days, times = [e.strip() for e in line.split("@")]
        dtstart, dtend = read_times(times)
        name = "Time " + line
        Timeslot.objects.get_or_create(
            name=name, day=days, start_time=dtstart, stop_time=dtend
        )
