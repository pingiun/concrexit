# Generated by Django 2.0.2 on 2018-07-08 16:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0021_emailchange'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='member',
            options={'ordering': ('first_name', 'last_name'), 'permissions': (('sentry_access', 'Access the Sentry backend'),)},
        ),
    ]