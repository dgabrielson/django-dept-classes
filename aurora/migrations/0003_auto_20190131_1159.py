# Generated by Django 2.1.5 on 2019-01-31 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("aurora", "0002_auto_20180528_1127")]

    operations = [
        migrations.AlterField(
            model_name="auroratimeslot",
            name="schedule_time",
            field=models.CharField(max_length=64),
        )
    ]
