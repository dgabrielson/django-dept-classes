# Generated by Django 2.0.1 on 2018-02-01 16:22

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("classes", "0019_auto_20180130_1542")]

    operations = [
        migrations.AlterModelOptions(
            name="timeslot",
            options={
                "base_manager_name": "objects",
                "ordering": ["day", "start_time", "stop_time"],
            },
        ),
        migrations.AlterField(
            model_name="timeslot",
            name="day",
            field=models.CharField(
                help_text='This should be a substring of "MTWRF".',
                max_length=16,
                validators=[
                    django.core.validators.RegexValidator(regex="M?T?W?R?F?S?")
                ],
            ),
        ),
    ]