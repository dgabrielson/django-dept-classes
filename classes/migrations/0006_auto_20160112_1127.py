# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-12 16:02
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("classes", "0005_auto_20160112_1002")]

    operations = [
        migrations.RemoveField(model_name="courseoutline", name="course"),
        migrations.RemoveField(model_name="courseoutline", name="term"),
    ]