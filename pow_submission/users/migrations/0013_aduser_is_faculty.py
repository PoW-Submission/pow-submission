# Generated by Django 3.1.2 on 2022-04-29 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_aduser_always_notify'),
    ]

    operations = [
        migrations.AddField(
            model_name='aduser',
            name='is_faculty',
            field=models.BooleanField(default=False),
        ),
    ]
