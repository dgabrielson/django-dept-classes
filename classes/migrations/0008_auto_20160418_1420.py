# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-18 19:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("classes", "0007_auto_20160418_1143")]

    operations = [
        migrations.AlterModelOptions(
            name="sectionhandout", options={"ordering": ["section", "label"]}
        ),
        migrations.AddField(
            model_name="sectionhandout",
            name="label",
            field=models.CharField(
                default="syllabus", help_text="Use lower case", max_length=128
            ),
        ),
    ]
