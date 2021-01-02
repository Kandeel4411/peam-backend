# Generated by Django 3.1.4 on 2021-01-02 23:19

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('title', models.CharField(max_length=50, verbose_name='Title')),
                ('description', models.CharField(blank=True, max_length=300, verbose_name='Description')),
                ('link', models.URLField(verbose_name='Link')),
            ],
            options={
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('author_name', models.CharField(max_length=50, verbose_name='Author Name')),
                ('description', models.CharField(blank=True, max_length=300, verbose_name='Description')),
                ('link', models.URLField(blank=True, verbose_name='Link')),
                ('type', models.CharField(max_length=20, verbose_name='Type')),
                ('unread', models.BooleanField(blank=True, default=False, verbose_name='Unread')),
                ('created_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'managed': True,
            },
        ),
    ]
