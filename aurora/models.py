# -*- encoding: utf-8
#######################
from __future__ import print_function, unicode_literals

from datetime import datetime, timedelta

from classes.models import (
    TERMS,
    Department,
    ScheduleType,
    Semester,
    SemesterDateRange,
    Timeslot,
)
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.encoding import python_2_unicode_compatible
from people.models import EmailAddress, Person
from places.models import ClassRoom

#######################

# Aurora models all map strings to other objects in the DataSphere...

AURORA_DATE_FMT = "%b %d, %Y"
AURORA_TIME_FMT = "%I:%M %p"

########################################################################


class AuroraCampusManager(models.Manager):
    """
    Provide is_blacklisted and is_online check-by-name utilities.
    These utility functions will auto-create campuses.

    By default, newly created campuses are blacklisted to prevent
    things seeping into the system by accident.
    """

    def is_blacklisted(self, name):
        """
        Returns True if the campus has been blacklisted, False otherwise
        """
        campus, created = self.get_or_create(name=name, defaults={"blacklisted": True})
        return campus.blacklisted

    def is_online(self, name):
        """
        Returns True if this is an online campus, False otherwise
        """
        campus, created = self.get_or_create(name=name, defaults={"blacklisted": True})
        return campus.online


@python_2_unicode_compatible
class AuroraCampus(models.Model):
    """
    Maps the instructor string from aurora to a person in the database.
    """

    name = models.CharField(max_length=128, help_text="The name the campus in aurora")
    blacklisted = models.BooleanField(
        default=False,
        help_text="Check this if you do not want to see courses for this campus",
    )
    online = models.BooleanField(
        default=False,
        help_text="Check this if the campus represents an online-only set of courses",
    )

    objects = AuroraCampusManager()

    class Meta:
        verbose_name_plural = "Aurora campuses"

    def __str__(self):
        return self.name


########################################################################


class AuroraDepartmentManager(models.Manager):
    def find(self, department_code, create=False):
        # check for a direct match

        obj = None
        created = False

        try:
            aurora_obj = self.get(department_code=department_code)
            obj = aurora_obj.department
        except AuroraDepartment.DoesNotExist:

            pass

        if obj is None:
            results_list = Department.objects.active().filter(code=department_code)
            try:
                obj = results_list.get()
            except Department.DoesNotExist:
                return None

        if obj is None and create:
            obj = self.create(department_code)
            created = True

        if obj is not None:
            self.get_or_create(department=obj, department_code=department_code)

        return obj, created

    def synchronize(self):
        """
        Return a queryset of objects to synchronize.
        """
        return self.filter(synchronize=True)

    def sync_codes(self):
        return self.synchronize().values_list("department_code", flat=True)


@python_2_unicode_compatible
class AuroraDepartment(models.Model):
    """
    Maps the instructor string from aurora to a person in the database.
    """

    department_code = models.CharField(max_length=16)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, limit_choices_to={"active": True}
    )
    synchronize = models.BooleanField(default=True)

    objects = AuroraDepartmentManager()

    def __str__(self):
        return self.department_code


########################################################################


class AuroraInstructorManager(models.Manager):
    def find(self, instructor, email_addr, create=False, verbosity=0):
        if verbosity > 2:
            print(
                'find(instructor="{}", email_addr="{}", create={}) -- start'.format(
                    instructor, email_addr, create
                )
            )
        person = None
        created = False
        # check for a direct match
        try:
            if verbosity > 2:
                print("Lookin for direct match.")
            aurora_obj = self.get(instructor=instructor)
            if verbosity > 2:
                print("Direct match found")
            person = aurora_obj.person
            if verbosity > 2:
                print("Early return; person = {}; created = {}".format(person, False))
            return person, False
        except AuroraInstructor.DoesNotExist:
            pass

        if verbosity > 2:
            print(
                'find(instructor="{}", email_addr="{}", create={}) -- no direct match'.format(
                    instructor, email_addr, create
                )
            )

        if person is None:
            # check for a matching person
            # will cause problems with some names
            if verbosity > 2:
                print("Looking for existing person")
            try:
                first, middle, last = instructor.split(None, 2)
            except ValueError:
                first, last = instructor.split(None, 1)
            if verbosity > 2:
                print('Using last="{}", first="{}"'.format(last, first))
            results_list = Person.objects.search(last, first)
            if verbosity > 2:
                print("Result list has {} candidates".format(results_list.count()))

            try:
                person = results_list.get()
                if verbosity > 2:
                    print("[2] person =", person)
            except Person.DoesNotExist:
                pass
            except Person.MultipleObjectsReturned:
                pass

        if person is None and email_addr is not None:
            if verbosity > 2:
                print("Looking by email address:", email_addr)

            try:
                person = Person.objects.get_by_email(email_addr)
                if verbosity > 2:
                    print("[3] person =", person)
            except EmailAddress.DoesNotExist:
                pass
            except EmailAddress.MultipleObjectsReturned as e:
                print("** Duplicate email address: {}".format(email_addr), flush=True)
                raise e

        if person is None and create:
            if verbosity > 2:
                print("Creating new person...")
            person = self.create_person(instructor, email_addr)
            if verbosity > 2:
                print("[4] person =", person)
            created = True
        if person is not None:
            if verbosity > 2:
                print("initializing mappin record")
            self.get_or_create(instructor=instructor, person=person)
            person.add_flag_by_name("instructor", "Available to instruct courses")
        if verbosity > 2:
            print("Late return; person = {}; created = {}".format(person, created))
        return person, created

    def create_person(self, name, email_addr):
        name = " ".join([part for part in name.split() if part != "."])
        defaults = Person.objects.guess_name_helper(name)
        defaults["slug"] = slugify(defaults["cn"])

        instructor = Person.objects.create(**defaults)
        if email_addr:
            email = instructor.add_email(email_addr, "work")
            email.public = True  # already available in a public system.
            email.save()
        instructor.add_flag_by_name("instructor", "Available to instruct courses")
        return instructor


@python_2_unicode_compatible
class AuroraInstructor(models.Model):
    """
    Maps the instructor string from aurora to a person in the database.
    """

    instructor = models.CharField(max_length=64)
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        limit_choices_to={"active": True, "flags__slug": "instructor"},
        help_text='Only people with the "instructor" flag are shown',
    )

    objects = AuroraInstructorManager()

    def __str__(self):
        return self.instructor + ": " + str(self.person)


########################################################################


class AuroraLocationManager(models.Manager):
    def find(self, location, create=False):

        classroom = None
        created = False
        # check for direct match:
        try:
            aurora_obj = self.get(location=location)
            classroom = aurora_obj.classroom
        except AuroraLocation.DoesNotExist:
            pass

        number, building = self.split_number_building(location)
        slug1 = slugify(number + " " + building)
        slug2 = slugify(location)
        if not classroom:
            # check for a matching classroom.
            try:
                classroom = ClassRoom.objects.get(slug=slug1)
            except ClassRoom.DoesNotExist:
                pass

        if not classroom:
            try:
                classroom = ClassRoom.objects.get(slug=slug2)
            except ClassRoom.DoesNotExist:
                pass

        if not classroom:
            try:
                classroom = ClassRoom.objects.get(
                    number=number, building__iexact=building
                )
            except ClassRoom.DoesNotExist:
                pass

        if classroom is None and create:
            classroom = self.create(location)
            created = True

        if classroom is not None:
            self.get_or_create(location=location, classroom=classroom)

        return classroom, created

    def split_number_building(self, location):
        # Q: How much of this logic is specific to the UofM's data entry?
        parts = location.split()
        if len(parts) < 2:
            assert False, "Strange location: {0!r}".format(location)
        number = parts[-1]
        building_parts = parts[:-1]
        if len(building_parts) > 0:
            if building_parts[-1] == "BUILDING":
                building_parts.pop()
            if building_parts[-1] == "LECTURE":
                building_parts.pop()
            if building_parts[-1] == "COLLEGE":
                building_parts.pop()
            if building_parts[0] == "EITC":
                building_parts = building_parts[1:] + [building_parts[0]]

            building = " ".join(building_parts)
        else:
            building = "-special"
        return number, building

    def create(self, location):

        slug = slugify(location)
        number, building = self.split_number_building(location)
        building = building.title().replace("'S", "'s").replace("’S", "'s")
        return ClassRoom.objects.create(number=number, building=building, slug=slug)


@python_2_unicode_compatible
class AuroraLocation(models.Model):
    """
    Maps the location string from aurora to a classroom in the database.
    """

    location = models.CharField(max_length=64)
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, limit_choices_to={"active": True}
    )

    objects = AuroraLocationManager()

    def __str__(self):
        return self.location + ": " + str(self.classroom)


########################################################################


class AuroraTimeslotManager(models.Manager):
    def read_times(self, schedule_time):
        start_time_str, finish_time_str = [
            e.strip() for e in schedule_time.split("-", 1)
        ]
        start_dt = datetime.strptime(start_time_str, AURORA_TIME_FMT)
        finish_dt = datetime.strptime(finish_time_str, AURORA_TIME_FMT)
        return start_dt.time(), finish_dt.time()

    def find(self, schedule_days, schedule_time, create=False):
        # check to see if we have a direct match...
        timeslot = None
        created = False

        try:
            aurora_obj = self.get(
                schedule_days=schedule_days, schedule_time=schedule_time
            )
            timeslot = aurora_obj.timeslot
        except AuroraTimeslot.DoesNotExist:
            pass

        if timeslot is None:
            # check to see if we can find a matching semester...
            start_time, stop_time = self.read_times(schedule_time)
            try:
                timeslot = Timeslot.objects.get(
                    day=schedule_days, start_time=start_time, stop_time=stop_time
                )
            except Timeslot.DoesNotExist:
                pass

        if timeslot is None and create:
            timeslot = self.create(schedule_days, schedule_time)
            created = True

        if timeslot is not None:
            self.get_or_create(
                schedule_days=schedule_days,
                schedule_time=schedule_time,
                timeslot=timeslot,
            )
        return timeslot, created

    def create(self, schedule_days, schedule_time):

        dtstart, dtend = self.read_times(schedule_time)
        name = "Time {0} @ {1}".format(schedule_days, schedule_time)
        timeslot = Timeslot.objects.create(
            name=name, day=schedule_days, start_time=dtstart, stop_time=dtend
        )
        return timeslot


@python_2_unicode_compatible
class AuroraTimeslot(models.Model):
    """
    Maps the days and time strings from the schedule section into a timeslot.
    """

    schedule_days = models.CharField(max_length=16)
    schedule_time = models.CharField(max_length=64)
    timeslot = models.ForeignKey(
        Timeslot, on_delete=models.CASCADE, limit_choices_to={"active": True}
    )

    objects = AuroraTimeslotManager()

    def __str__(self):
        return (
            self.schedule_days + " @ " + self.schedule_time + ": " + str(self.timeslot)
        )


########################################################################


class AuroraDateRangeManager(models.Manager):
    def breakout_data(self, schedule_date_range):
        start_date_str, finish_date_str = [
            e.strip() for e in schedule_date_range.split("-", 1)
        ]
        start_dt = datetime.strptime(start_date_str, AURORA_DATE_FMT)
        finish_dt = datetime.strptime(finish_date_str, AURORA_DATE_FMT)

        return {"start": start_dt.date(), "finish": finish_dt.date()}

    def guess_semester(self, data):
        """
        Data as returned by breakout_data(); both start and finish
        must be within the same semester otherwise this returns None.
        """
        start_term = Semester.objects.get_by_date(data["start"])
        finish_term = Semester.objects.get_by_date(data["finish"])
        if start_term == finish_term:
            return start_term
        return None

    def find(self, schedule_date_range, create=False):
        date_range = None
        created = False
        # check to see if we have a direct match...
        try:
            obj = self.get(schedule_date_range=schedule_date_range)
            date_range = obj.date_range
        except AuroraDateRange.DoesNotExist:
            pass

        if date_range is None:
            # check to see if we can find a matching semester...
            data = self.breakout_data(schedule_date_range)
            try:
                date_range = SemesterDateRange.objects.get(**data)
            except SemesterDateRange.DoesNotExist:
                pass
            if date_range is None and create:
                # to create, we need a semester object as well...
                semester = self.guess_semester(data)
                if semester is not None:
                    data["semester"] = semester
                    date_range = SemesterDateRange.objects.create(**data)
                    created = True

        if date_range is not None:
            self.get_or_create(
                schedule_date_range=schedule_date_range, date_range=date_range
            )
        return date_range, created

    def create(self, schedule_date_range):
        data = self.breakout_data(schedule_date_range)
        date_range = SemesterDateRange.objects.find(**data)
        self.get_or_create(
            schedule_date_range=schedule_date_range, date_range=date_range
        )
        return date_range


@python_2_unicode_compatible
class AuroraDateRange(models.Model):
    """
    Maps the associated_term and schedule_date_range strings into a semester.
    """

    schedule_date_range = models.CharField(max_length=64)
    date_range = models.ForeignKey(
        SemesterDateRange,
        on_delete=models.CASCADE,
        limit_choices_to={"semester__active": True},
    )

    objects = AuroraDateRangeManager()

    def __str__(self):
        return self.schedule_date_range + ": " + str(self.date_range)


########################################################################
########################################################################
