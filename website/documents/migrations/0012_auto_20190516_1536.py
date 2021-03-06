# Generated by Django 2.2.1 on 2019-05-16 13:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0011_auto_20190327_1948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='file_en',
            field=models.FileField(upload_to='documents/', validators=[django.core.validators.FileExtensionValidator(['txt', 'pdf', 'jpg', 'jpeg', 'png'])], verbose_name='file (EN)'),
        ),
        migrations.AlterField(
            model_name='document',
            name='file_nl',
            field=models.FileField(upload_to='documents/', validators=[django.core.validators.FileExtensionValidator(['txt', 'pdf', 'jpg', 'jpeg', 'png'])], verbose_name='file (NL)'),
        ),
    ]
