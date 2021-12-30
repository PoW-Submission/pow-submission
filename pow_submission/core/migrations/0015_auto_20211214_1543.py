# Generated by Django 3.1.2 on 2021-12-14 15:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0014_auto_20211203_1452'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('courses', models.ManyToManyField(blank=True, to='core.Course')),
            ],
        ),
        migrations.AlterField(
            model_name='termplan',
            name='approval',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='termplan',
            name='student',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='termplan',
            name='term',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='core.term'),
        ),
        migrations.CreateModel(
            name='Track',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100, unique=True)),
                ('categories', models.ManyToManyField(blank=True, to='core.Category')),
                ('courses', models.ManyToManyField(blank=True, to='core.Course')),
                ('startTerm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.term')),
            ],
        ),
    ]
