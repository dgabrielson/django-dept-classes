# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-23 14:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("classes", "0012_auto_20160629_1510")]

    operations = [
        migrations.AddField(
            model_name="enrollment",
            name="waitlist_capacity",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="waitlist_registration",
            field=models.IntegerField(default=0),
        ),
    ]