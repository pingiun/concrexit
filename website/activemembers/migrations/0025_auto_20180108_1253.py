# Generated by Django 2.0.1 on 2018-01-08 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activemembers', '0024_auto_20171129_2129'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='board',
            managers=[
                ('objects', models.manager.Manager()),
            ],
        ),
    ]
