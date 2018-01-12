# Generated by Django 2.0.1 on 2018-01-12 11:14

from django.db import migrations, models
import django.db.models.deletion
import events.models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0024_auto_20180111_1039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registration',
            name='member',
            field=models.ForeignKey(blank=True, limit_choices_to=events.models.registration_member_choices_limit, null=True, on_delete=django.db.models.deletion.CASCADE, to='members.Member'),
        ),
    ]
