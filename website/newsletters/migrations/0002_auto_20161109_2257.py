# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-09 21:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletters', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletterevent',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=5, null=True, verbose_name='Price (in Euro)'),
        ),
    ]