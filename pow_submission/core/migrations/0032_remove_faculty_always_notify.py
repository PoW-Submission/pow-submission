# Generated by Django 3.1.2 on 2022-04-15 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_auto_20220415_1456'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='faculty',
            name='always_notify',
        ),
    ]