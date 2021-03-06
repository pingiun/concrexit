# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-09 20:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0012_auto_20161104_2119'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='blacklisted',
            field=models.CharField(choices=[('all', 'All events'), ('no_events', 'User may not attend events'), ('no_drinks', 'User may not attend drinks'), ('nothing', 'User may not attend anything')], default='all', max_length=9, verbose_name='Which events can this member attend'),
        ),
    ]
