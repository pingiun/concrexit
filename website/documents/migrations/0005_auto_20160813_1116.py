# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-13 09:16
from __future__ import unicode_literals

from django.db import migrations, models
import documents.models
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_auto_20160725_2346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalmeetingdocument',
            name='file',
            field=models.FileField(upload_to=documents.models.meetingdocument_upload_to, validators=[utils.validators.validate_file_extension]),
        ),
    ]