# Generated by Django 3.1.2 on 2022-04-11 17:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20220408_1910'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='edittext',
            name='response',
        ),
        migrations.AlterUniqueTogether(
            name='qgroup',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='qgroup',
            name='questions',
        ),
        migrations.RemoveField(
            model_name='qgroup',
            name='section',
        ),
        migrations.RemoveField(
            model_name='question',
            name='canned_no',
        ),
        migrations.RemoveField(
            model_name='question',
            name='canned_yes',
        ),
        migrations.AlterUniqueTogether(
            name='response',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='response',
            name='form',
        ),
        migrations.RemoveField(
            model_name='response',
            name='question',
        ),
        migrations.DeleteModel(
            name='ContactQuestion',
        ),
        migrations.DeleteModel(
            name='CustomQuestion',
        ),
        migrations.DeleteModel(
            name='FreeTextQuestion',
        ),
        migrations.DeleteModel(
            name='IntegerQuestion',
        ),
        migrations.DeleteModel(
            name='MultiSelectQuestion',
        ),
        migrations.DeleteModel(
            name='TextListQuestion',
        ),
        migrations.DeleteModel(
            name='YesNoExplainQuestion',
        ),
        migrations.DeleteModel(
            name='YesNoQuestion',
        ),
        migrations.DeleteModel(
            name='CannedText',
        ),
        migrations.DeleteModel(
            name='ConsentForm',
        ),
        migrations.DeleteModel(
            name='EditText',
        ),
        migrations.DeleteModel(
            name='QGroup',
        ),
        migrations.DeleteModel(
            name='Question',
        ),
        migrations.DeleteModel(
            name='Response',
        ),
        migrations.DeleteModel(
            name='Section',
        ),
    ]