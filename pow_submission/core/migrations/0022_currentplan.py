# Generated by Django 3.1.2 on 2022-01-09 17:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0021_faculty_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CurrentPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.course')),
                ('offering', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.offering')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('termPlan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currentPlans', to='core.termplan')),
            ],
        ),
    ]