# Generated by Django 3.1.2 on 2022-01-05 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_faculty'),
    ]

    operations = [
        migrations.AddField(
            model_name='faculty',
            name='name',
            field=models.TextField(default='Temp'),
            preserve_default=False,
        ),
    ]
