# -*- coding: utf-8 -*-
#######################
from __future__ import print_function, unicode_literals

from django.db import migrations, models

#######################


class Migration(migrations.Migration):

    dependencies = [
        ("classes", "0001_initial"),
        ("places", "0001_initial"),
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuroraCampus",
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
                    "name",
                    models.CharField(
                        help_text=b"The name the campus in aurora", max_length=128
                    ),
                ),
                (
                    "blacklisted",
                    models.BooleanField(
                        default=False,
                        help_text=b"Check this if you do not want to see courses for this campus",
                    ),
                ),
                (
                    "online",
                    models.BooleanField(
                        default=False,
                        help_text=b"Check this if the campus represents an online-only set of courses",
                    ),
                ),
            ],
            options={"verbose_name_plural": "Aurora campuses"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AuroraDateRange",
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
                ("schedule_date_range", models.CharField(max_length=64)),
                (
                    "date_range",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        to="classes.SemesterDateRange",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AuroraDepartment",
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
                ("department_code", models.CharField(max_length=16)),
                ("synchronize", models.BooleanField(default=True)),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="classes.Department"
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AuroraInstructor",
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
                ("instructor", models.CharField(max_length=64)),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        help_text=b'Only people with the "instructor" flag are shown',
                        to="people.Person",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AuroraLocation",
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
                ("location", models.CharField(max_length=64)),
                (
                    "classroom",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="places.ClassRoom"
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AuroraTimeslot",
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
                ("schedule_days", models.CharField(max_length=16)),
                ("schedule_time", models.CharField(max_length=32)),
                (
                    "timeslot",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="classes.Timeslot"
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
