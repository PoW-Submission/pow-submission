# Generated by Django 3.1.2 on 2022-04-08 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20220404_1907'),
    ]

    operations = [
        migrations.AddField(
            model_name='track',
            name='program',
            field=models.CharField(default='MS', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='track',
            name='requiredHours',
            field=models.FloatField(default=0),
        ),
    ]
