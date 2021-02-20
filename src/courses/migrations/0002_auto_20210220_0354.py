# Generated by Django 3.1.4 on 2021-02-20 03:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamstudent',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='uid'),
        ),
        migrations.AddField(
            model_name='teamstudent',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.team', to_field='uid'),
        ),
        migrations.AddField(
            model_name='teaminvitation',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='uid'),
        ),
        migrations.AddField(
            model_name='teaminvitation',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='courses.team', to_field='uid'),
        ),
        migrations.AddField(
            model_name='team',
            name='requirement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='courses.projectrequirement', to_field='uid'),
        ),
        migrations.AddField(
            model_name='team',
            name='students',
            field=models.ManyToManyField(related_name='teams', through='courses.TeamStudent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='projectrequirementattachment',
            name='requirement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='courses.projectrequirement', to_field='uid'),
        ),
        migrations.AddField(
            model_name='projectrequirement',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requirements', to='courses.course', to_field='uid'),
        ),
        migrations.AddField(
            model_name='courseteacher',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course', to_field='uid'),
        ),
        migrations.AddField(
            model_name='courseteacher',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='uid'),
        ),
        migrations.AddField(
            model_name='coursestudent',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course', to_field='uid'),
        ),
        migrations.AddField(
            model_name='coursestudent',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='uid'),
        ),
        migrations.AddField(
            model_name='courseinvitation',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='courses.course', to_field='uid'),
        ),
        migrations.AddField(
            model_name='courseinvitation',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='uid'),
        ),
        migrations.AddField(
            model_name='courseattachment',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='courses.course', to_field='uid'),
        ),
        migrations.AddField(
            model_name='course',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to=settings.AUTH_USER_MODEL, to_field='uid'),
        ),
        migrations.AddField(
            model_name='course',
            name='students',
            field=models.ManyToManyField(related_name='as_student_set', through='courses.CourseStudent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='course',
            name='teachers',
            field=models.ManyToManyField(related_name='as_teacher_set', through='courses.CourseTeacher', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='teamstudent',
            constraint=models.UniqueConstraint(fields=('student', 'team'), name='unique_team_student'),
        ),
        migrations.AddConstraint(
            model_name='teaminvitation',
            constraint=models.CheckConstraint(check=models.Q(created_at__lte=django.db.models.expressions.F('expiry_date')), name='teaminvitation_expiry_date_constraint'),
        ),
        migrations.AddConstraint(
            model_name='teaminvitation',
            constraint=models.CheckConstraint(check=models.Q(status__in=['Pending', 'Accepted', 'Rejected', 'Expired']), name='teaminvitation_status_constraint'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['requirement'], name='courses_tea_require_bc3ffe_idx'),
        ),
        migrations.AddConstraint(
            model_name='team',
            constraint=models.UniqueConstraint(fields=('name', 'requirement'), name='unique_team'),
        ),
        migrations.AddConstraint(
            model_name='projectrequirement',
            constraint=models.CheckConstraint(check=models.Q(from_dt__lte=django.db.models.expressions.F('to_dt')), name='date_constraint'),
        ),
        migrations.AddConstraint(
            model_name='projectrequirement',
            constraint=models.UniqueConstraint(fields=('title', 'course'), name='unique_project_requirement'),
        ),
        migrations.AddConstraint(
            model_name='courseteacher',
            constraint=models.UniqueConstraint(fields=('course', 'teacher'), name='unique_course_Teacher'),
        ),
        migrations.AddConstraint(
            model_name='coursestudent',
            constraint=models.UniqueConstraint(fields=('student', 'course'), name='unique_course_student'),
        ),
        migrations.AddConstraint(
            model_name='courseinvitation',
            constraint=models.CheckConstraint(check=models.Q(created_at__lte=django.db.models.expressions.F('expiry_date')), name='courseinvitation_expiry_date_constraint'),
        ),
        migrations.AddConstraint(
            model_name='courseinvitation',
            constraint=models.CheckConstraint(check=models.Q(status__in=['Pending', 'Accepted', 'Rejected', 'Expired']), name='courseinvitation_status_constraint'),
        ),
        migrations.AddConstraint(
            model_name='courseinvitation',
            constraint=models.CheckConstraint(check=models.Q(type__in=['student', 'teacher']), name='courseinvitation_type_constraint'),
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['owner'], name='courses_cou_owner_i_f32810_idx'),
        ),
        migrations.AddConstraint(
            model_name='course',
            constraint=models.UniqueConstraint(fields=('owner', 'code'), name='unique_course'),
        ),
    ]