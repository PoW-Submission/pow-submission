# Generated by Django 3.1.2 on 2021-12-03 14:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_plannedwork_term'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plannedwork',
            name='term',
        ),
        migrations.AddField(
            model_name='plannedwork',
            name='termPlan',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='core.termplan'),
            preserve_default=False,
        ),
    ]