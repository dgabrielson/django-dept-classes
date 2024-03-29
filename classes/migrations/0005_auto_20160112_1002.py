# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-12 16:02
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("classes", "0004_auto_20160112_0912")]

    operations = [
        migrations.AlterModelOptions(
            name="courseoutline",
            options={"ordering": ["section"], "verbose_name": "Course Outline"},
        ),
        migrations.AlterField(
            model_name="courseoutline",
            name="section",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="classes.Section"
            ),
        ),
    ]
