# Generated by Django 3.1.4 on 2021-01-02 23:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0002_auto_20210102_2319'),
        ('courses', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseteacher',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.teacher', to_field='uid'),
        ),
        migrations.AddField(
            model_name='courseattachment',
            name='attachment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.attachment', to_field='uid'),
        ),
        migrations.AddField(
            model_name='courseattachment',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachment', to='courses.course', to_field='uid'),
        ),
        migrations.AlterUniqueTogether(
            name='courseteacher',
            unique_together={('teacher', 'course')},
        ),
    ]
