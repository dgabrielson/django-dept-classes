# Generated by Django 2.0.5 on 2018-05-28 16:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("aurora", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="auroracampus",
            name="blacklisted",
            field=models.BooleanField(
                default=False,
                help_text="Check this if you do not want to see courses for this campus",
            ),
        ),
        migrations.AlterField(
            model_name="auroracampus",
            name="name",
            field=models.CharField(
                help_text="The name the campus in aurora", max_length=128
            ),
        ),
        migrations.AlterField(
            model_name="auroracampus",
            name="online",
            field=models.BooleanField(
                default=False,
                help_text="Check this if the campus represents an online-only set of courses",
            ),
        ),
        migrations.AlterField(
            model_name="auroradaterange",
            name="date_range",
            field=models.ForeignKey(
                limit_choices_to={"semester__active": True},
                on_delete=django.db.models.deletion.CASCADE,
                to="classes.SemesterDateRange",
            ),
        ),
        migrations.AlterField(
            model_name="auroradepartment",
            name="department",
            field=models.ForeignKey(
                limit_choices_to={"active": True},
                on_delete=django.db.models.deletion.CASCADE,
                to="classes.Department",
            ),
        ),
        migrations.AlterField(
            model_name="aurorainstructor",
            name="person",
            field=models.ForeignKey(
                help_text='Only people with the "instructor" flag are shown',
                limit_choices_to={"active": True, "flags__slug": "instructor"},
                on_delete=django.db.models.deletion.CASCADE,
                to="people.Person",
            ),
        ),
        migrations.AlterField(
            model_name="auroralocation",
            name="classroom",
            field=models.ForeignKey(
                limit_choices_to={"active": True},
                on_delete=django.db.models.deletion.CASCADE,
                to="places.ClassRoom",
            ),
        ),
        migrations.AlterField(
            model_name="auroratimeslot",
            name="timeslot",
            field=models.ForeignKey(
                limit_choices_to={"active": True},
                on_delete=django.db.models.deletion.CASCADE,
                to="classes.Timeslot",
            ),
        ),
    ]
