# Generated by Django 3.1.4 on 2020-12-28 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('courses', '0002_auto_20201228_1209'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teammember',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.student'),
        ),
        migrations.AddField(
            model_name='teammember',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.team'),
        ),
        migrations.AddField(
            model_name='team',
            name='requirement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.projectrequirement'),
        ),
        migrations.AlterUniqueTogether(
            name='teammember',
            unique_together={('student', 'team')},
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('name', 'requirement')},
        ),
    ]
