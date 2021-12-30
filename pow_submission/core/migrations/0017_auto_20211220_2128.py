# Generated by Django 3.1.2 on 2021-12-20 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20211214_2130'),
    ]

    operations = [
        migrations.AddField(
            model_name='termplan',
            name='approver',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='plannedwork',
            name='termPlan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plannedWorks', to='core.termplan'),
        ),
    ]
