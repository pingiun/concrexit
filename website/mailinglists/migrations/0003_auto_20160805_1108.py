# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-05 09:08
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailinglists', '0002_auto_20160805_1101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listalias',
            name='alias',
            field=models.CharField(max_length=100, validators=[django.core.validators.RegexValidator(message='Enter a [a-zA-Z0-9] name', regex='[a-zA-Z0-9]+')]),
        ),
        migrations.AlterField(
            model_name='mailinglist',
            name='name',
            field=models.CharField(max_length=100, validators=[django.core.validators.RegexValidator(message='Enter a [a-zA-Z0-9] name', regex='[a-zA-Z0-9]+')]),
        ),
    ]