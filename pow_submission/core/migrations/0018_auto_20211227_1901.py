# Generated by Django 3.1.2 on 2021-12-27 19:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20211220_2128'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offering',
            name='term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='core.term'),
        ),
    ]
