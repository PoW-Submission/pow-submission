# Generated by Django 3.1.2 on 2020-10-04 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20200922_1855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aduser',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='first name'),
        ),
    ]
