# Generated by Django 2.1.5 on 2019-01-30 19:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0009_auto_20181219_2104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='uploader',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.Member', verbose_name='uploader'),
        ),
        migrations.AlterField(
            model_name='summary',
            name='uploader',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.Member', verbose_name='uploader'),
        ),
    ]
