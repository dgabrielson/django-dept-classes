# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("places", "0001_initial"), ("people", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                ("code", models.CharField(max_length=10)),
                ("name", models.CharField(max_length=150)),
                (
                    "slug",
                    models.SlugField(
                        help_text="A url fragment which identies this course",
                        unique=True,
                    ),
                ),
                ("description", models.TextField(blank=True)),
            ],
            options={"ordering": ["department", "code"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="CourseOutline",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                ("path", models.FileField(upload_to="outlines/%Y/%m")),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="classes.Course"
                    ),
                ),
            ],
            options={"ordering": ["course", "-term"], "verbose_name": "Course Outline"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="A short character sequence which is used to construct course names, e.g., BIOL or GRAD",
                        max_length=16,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text=b"Verbose name of the department, e.g., 'Biology' or 'Graduate Studies'",
                        max_length=64,
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="A url which identifies the department", unique=True
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "advertised",
                    models.BooleanField(
                        default=True,
                        help_text="A department should be advertised if you are authoritive for it",
                    ),
                ),
                (
                    "public",
                    models.BooleanField(
                        default=True,
                        help_text=b"If a department is public, then it's course pages are available",
                    ),
                ),
            ],
            options={"ordering": ["code"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                ("capacity", models.IntegerField()),
                (
                    "registration",
                    models.IntegerField(verbose_name="Actual registration"),
                ),
            ],
            options={"get_latest_by": "created"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ImportantDate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                (
                    "date",
                    models.DateField(
                        help_text='See <a href="http://umanitoba.ca/calendar">the UofM calendar / Academic Schedule</a>, <a href="http://umanitoba.ca/student/records/deadlines/">student records</a> and and <a href="http://umanitoba.ca/summer">Summer Session / Important Dates</a> for dates.'
                    ),
                ),
                (
                    "end_date",
                    models.DateField(
                        help_text="Specify the end date for things like reading week, which last for more than one day.",
                        null=True,
                        blank=True,
                    ),
                ),
                ("title", models.CharField(max_length=250)),
                ("no_class", models.BooleanField(default=False)),
                ("university_closed", models.BooleanField(default=False)),
            ],
            options={"ordering": ["date"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ScheduleType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                ("name", models.CharField(max_length=64)),
                ("ordering", models.PositiveSmallIntegerField(default=50)),
            ],
            options={"ordering": ["ordering", "name"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Section",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                ("section_name", models.CharField(max_length=4)),
                (
                    "slug",
                    models.SlugField(
                        help_text="A url fragment which identies this section",
                        unique=True,
                    ),
                ),
                ("crn", models.CharField(max_length=10, verbose_name="CRN")),
                (
                    "note",
                    models.CharField(
                        help_text="Additional section information or details, e.g., for topics courses",
                        max_length=512,
                        blank=True,
                    ),
                ),
                (
                    "override_instructor",
                    models.BooleanField(
                        default=False,
                        help_text="If this is set, then the instructor will not be changed by any automatic update",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="classes.Course"
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        blank=True,
                        to="people.Person",
                        help_text='Only people with the "instructor" flag are shown',
                        null=True,
                    ),
                ),
            ],
            options={"ordering": ["term", "course", "section_name"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="SectionSchedule",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                (
                    "override_room",
                    models.BooleanField(
                        default=False,
                        help_text="If this is set, then the room will not be changed by any automatic update",
                    ),
                ),
                (
                    "override_instructor",
                    models.BooleanField(
                        default=False,
                        help_text="If this is set, then the instructor will not be changed by any automatic update",
                    ),
                ),
            ],
            options={"ordering": ["section", "date_range", "type"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Semester",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                ("year", models.SmallIntegerField(default=2014)),
                (
                    "term",
                    models.CharField(
                        max_length=2,
                        choices=[(b"1", b"Winter"), (b"2", b"Summer"), (b"3", b"Fall")],
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="A url fragment which identifies this semester",
                        unique=True,
                    ),
                ),
                (
                    "advertised",
                    models.BooleanField(
                        default=False,
                        help_text="A semester should be advertised if relevant information should be displayed.",
                    ),
                ),
            ],
            options={"ordering": ["year", "term"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="SemesterDateRange",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                (
                    "start",
                    models.DateField(
                        help_text='First day of classes.  See <a href="http://umanitoba.ca/calendar">the UofM calendar / Academic Schedule</a> for dates.'
                    ),
                ),
                ("finish", models.DateField(help_text="Last day of classes.")),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="classes.Semester"
                    ),
                ),
            ],
            options={"ordering": ["start", "finish"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Timeslot",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck this to remove this item without actually deleting it.",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation time"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="last modification time"
                    ),
                ),
                ("name", models.CharField(max_length=32)),
                (
                    "day",
                    models.CharField(
                        help_text='This should be a substring of "MTWRF".',
                        max_length=16,
                    ),
                ),
                ("start_time", models.TimeField()),
                ("stop_time", models.TimeField()),
            ],
            options={"ordering": ["name"]},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="timeslot", unique_together=set([("day", "start_time", "stop_time")])
        ),
        migrations.AddField(
            model_name="sectionschedule",
            name="date_range",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                blank=True,
                to="classes.SemesterDateRange",
                null=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="sectionschedule",
            name="instructor",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                blank=True,
                to="people.Person",
                help_text='Only people with the "instructor" flag are shown',
                null=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="sectionschedule",
            name="room",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="places.ClassRoom"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="sectionschedule",
            name="section",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="classes.Section"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="sectionschedule",
            name="timeslot",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="classes.Timeslot"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="sectionschedule",
            name="type",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="classes.ScheduleType"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="section",
            name="term",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="classes.Semester"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="enrollment",
            name="section",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="classes.Section"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="courseoutline",
            name="term",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="classes.Semester"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="course",
            name="department",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="classes.Department", null=True
            ),
            preserve_default=True,
        ),
    ]
