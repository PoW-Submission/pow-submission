# Generated by Django 3.1.2 on 2022-03-23 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_aduser_always_notify'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aduser',
            name='always_notify',
            field=models.BooleanField(default=False),
        ),
    ]
