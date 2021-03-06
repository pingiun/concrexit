# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-12 08:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def forward_func(apps, schema_editor):
    Registration = apps.get_model('events', 'Registration')

    for registration in Registration.objects.all():
        if registration.member_old:
            registration.member = registration.member_old.user
            registration.save(update_fields=('member',))


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_2_user_foreign_keys'),
    ]

    operations = [
        migrations.RunPython(
            code=forward_func,
        ),
    ]
