# Generated by Django 2.0.9 on 2018-11-11 16:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0027_auto_20181024_2000'),
        ('events', '0027_merge_20180618_1438'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='registration',
            unique_together={('member', 'event')},
        ),
    ]