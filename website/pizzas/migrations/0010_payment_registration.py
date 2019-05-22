# Generated by Django 2.2 on 2019-04-13 20:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pizzas', '0009_payment_registration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='paid',
        ),
        migrations.AlterField(
            model_name='order',
            name='payment',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pizzas_order', to='payments.Payment', verbose_name='payment'),
        ),
    ]