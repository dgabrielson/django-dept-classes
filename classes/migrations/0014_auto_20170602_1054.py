# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-02 15:54
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("classes", "0013_auto_20160823_0917")]

    operations = [
        migrations.AlterModelOptions(
            name="course",
            options={
                "base_manager_name": "objects",
                "ordering": ["department", "code"],
            },
        ),
        migrations.AlterModelOptions(
            name="coursehandout",
            options={
                "base_manager_name": "objects",
                "ordering": ["course", "ordering", "label"],
            },
        ),
        migrations.AlterModelOptions(
            name="department",
            options={"base_manager_name": "objects", "ordering": ["code"]},
        ),
        migrations.AlterModelOptions(
            name="section",
            options={
                "base_manager_name": "objects",
                "ordering": ["term", "course", "section_name"],
            },
        ),
        migrations.AlterModelOptions(
            name="sectionhandout",
            options={
                "base_manager_name": "objects",
                "ordering": ["section", "ordering", "label"],
            },
        ),
        migrations.AlterModelOptions(
            name="sectionschedule",
            options={
                "base_manager_name": "objects",
                "ordering": ["section", "date_range", "type"],
            },
        ),
        migrations.AlterModelOptions(
            name="semester",
            options={"base_manager_name": "objects", "ordering": ["year", "term"]},
        ),
        migrations.AlterModelOptions(
            name="semesterdaterange",
            options={"base_manager_name": "objects", "ordering": ["start", "finish"]},
        ),
        migrations.AlterModelOptions(
            name="timeslot",
            options={"base_manager_name": "objects", "ordering": ["name"]},
        ),
        migrations.AlterField(
            model_name="course",
            name="department",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="classes.Department",
            ),
        ),
        migrations.AlterField(
            model_name="coursehandout",
            name="course",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.Course"
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="course",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.Course"
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="instructor",
            field=models.ForeignKey(
                blank=True,
                help_text='Only people with the "instructor" flag are shown',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="people.Person",
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="term",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.Semester"
            ),
        ),
        migrations.AlterField(
            model_name="sectionhandout",
            name="section",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.Section"
            ),
        ),
        migrations.AlterField(
            model_name="sectionschedule",
            name="date_range",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="classes.SemesterDateRange",
            ),
        ),
        migrations.AlterField(
            model_name="sectionschedule",
            name="instructor",
            field=models.ForeignKey(
                blank=True,
                help_text='Only people with the "instructor" flag are shown',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="people.Person",
            ),
        ),
        migrations.AlterField(
            model_name="sectionschedule",
            name="room",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="places.ClassRoom"
            ),
        ),
        migrations.AlterField(
            model_name="sectionschedule",
            name="section",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.Section"
            ),
        ),
        migrations.AlterField(
            model_name="sectionschedule",
            name="timeslot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.Timeslot"
            ),
        ),
        migrations.AlterField(
            model_name="sectionschedule",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.ScheduleType"
            ),
        ),
        migrations.AlterField(
            model_name="semester",
            name="year",
            field=models.SmallIntegerField(default=2017),
        ),
        migrations.AlterField(
            model_name="semesterdaterange",
            name="semester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="classes.Semester"
            ),
        ),
    ]