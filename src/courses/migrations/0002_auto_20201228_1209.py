# Generated by Django 3.1.4 on 2020-12-28 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('courses', '0001_initial'),
        ('core', '0002_auto_20201228_1209'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseteacher',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.teacher'),
        ),
        migrations.AddField(
            model_name='courseattachment',
            name='attachment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.attachment'),
        ),
        migrations.AddField(
            model_name='courseattachment',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course'),
        ),
        migrations.AlterUniqueTogether(
            name='courseteacher',
            unique_together={('teacher', 'course')},
        ),
    ]
