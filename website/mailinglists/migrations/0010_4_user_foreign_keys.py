# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-12 10:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailinglists', '0010_3_user_foreign_keys'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mailinglist',
            name='members_old',
        ),
    ]
