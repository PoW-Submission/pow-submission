# Generated by Django 3.1.2 on 2022-04-15 14:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20220323_1531'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aduser',
            name='always_notify',
        ),
    ]
