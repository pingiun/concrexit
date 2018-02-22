# Generated by Django 2.0.2 on 2018-02-21 18:24

from django.db import migrations, models
import django.db.models.deletion
import pushnotifications.models


class Migration(migrations.Migration):

    dependencies = [
        ('pushnotifications', '0003_message_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('key', models.CharField(max_length=16, primary_key=True, serialize=False)),
                ('name_en', models.CharField(max_length=32, verbose_name='name (EN)')),
                ('name_nl', models.CharField(max_length=32, verbose_name='name (NL)')),
            ],
        ),
        migrations.AlterField(
            model_name='message',
            name='category',
            field=models.ForeignKey(default='general', on_delete=django.db.models.deletion.CASCADE, to='pushnotifications.Category', verbose_name='category'),
        ),
        migrations.AddField(
            model_name='device',
            name='receive_category',
            field=models.ManyToManyField(default=pushnotifications.models.Device.default_receive_category, to='pushnotifications.Category'),
        ),
    ]
