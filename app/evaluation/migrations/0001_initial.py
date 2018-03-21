# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-03-20 18:38
from __future__ import unicode_literals

import uuid

import django.db.models.deletion
import social_django.fields
from django.conf import settings
from django.db import migrations, models

import evaluation.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenges', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('use_teams', models.BooleanField(default=False, help_text='If true, users are able to form teams together to participate in challenges.')),
                ('score_jsonpath', models.CharField(blank=True, help_text='The jsonpath of the field in metrics.json that will be used for the overall scores on the results page. See http://goessner.net/articles/JsonPath/ for syntax. For example:\n\ndice.mean', max_length=255)),
                ('score_title', models.CharField(default='Score', help_text='The name that will be displayed for the scores column, for instance:\n\nScore (log-loss)', max_length=32)),
                ('score_default_sort', models.CharField(choices=[('asc', 'Ascending'), ('desc', 'Descending')], default='desc', help_text='The default sorting to use for the scores on the results page.', max_length=4)),
                ('extra_results_columns', social_django.fields.JSONField(default=dict, help_text='A JSON object that contains the extra columns from metrics.json that will be displayed on the results page. Where the KEYS contain the titles of the columns, and the VALUES contain the JsonPath to the corresponding metric in metrics.json. For example:\n\n{"Accuracy": "aggregates.acc","Dice": "dice.mean"}')),
                ('allow_submission_comments', models.BooleanField(default=False, help_text='Allow users to submit comments as part of their submission.')),
                ('allow_supplementary_file', models.BooleanField(default=False, help_text='Show a supplementary file field on the submissions page so that users can upload an additional file along with their predictions file as part of their submission (eg, include a pdf description of their method).')),
                ('require_supplementary_file', models.BooleanField(default=False, help_text='Force users to upload a supplementary file with their predictions file.')),
                ('supplementary_file_label', models.CharField(blank=True, default='Supplementary File', help_text='The label that will be used on the submission and results page for the supplementary file. For example: Algorithm Description.', max_length=32)),
                ('supplementary_file_help_text', models.CharField(blank=True, default='', help_text='The help text to include on the submissions page to describe the submissions file. Eg: "A PDF description of the method.".', max_length=128)),
                ('show_supplementary_file_link', models.BooleanField(default=False, help_text='Show a link to download the supplementary file on the results page.')),
                ('daily_submission_limit', models.PositiveIntegerField(default=10, help_text='The limit on the number of times that a user can make a submission in a 24 hour period.')),
                ('challenge', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_config', to='challenges.ComicSite')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'The task is waiting for execution'), (1, 'The task has been started'), (2, 'The task is to be retried, possibly because of failure'), (3, 'The task raised an exception, or has exceeded the retry limit'), (4, 'The task executed successfully'), (5, 'The task was cancelled')], default=0)),
                ('status_history', social_django.fields.JSONField(default=dict)),
                ('output', models.TextField()),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.ComicSite')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Method',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('ready', models.BooleanField(default=False, editable=False, help_text='Is this method ready to be used?')),
                ('status', models.TextField(editable=False)),
                ('image', models.FileField(help_text='Tar archive of the container image produced from the command `docker save IMAGE > IMAGE.tar`. See https://docs.docker.com/engine/reference/commandline/save/', upload_to=evaluation.models.method_image_path, validators=[evaluation.validators.ExtensionValidator(allowed_extensions=('.tar',))])),
                ('image_sha256', models.CharField(editable=False, max_length=71)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.ComicSite')),
                ('creator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('metrics', social_django.fields.JSONField(default=dict)),
                ('public', models.BooleanField(default=True)),
                ('rank', models.PositiveIntegerField(default=0, help_text='The position of this result on the leaderboard. If the value is zero, then the result is unranked.')),
                ('absolute_url', models.TextField(blank=True, editable=False)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.ComicSite')),
                ('job', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='evaluation.Job')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResultScreenshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(upload_to=evaluation.models.result_screenshot_path)),
                ('result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evaluation.Result')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to=evaluation.models.submission_file_path, validators=[evaluation.validators.MimeTypeValidator(allowed_types=('application/zip', 'text/plain')), evaluation.validators.ExtensionValidator(allowed_extensions=('.zip', '.csv'))])),
                ('supplementary_file', models.FileField(blank=True, upload_to=evaluation.models.submission_supplementary_file_path, validators=[evaluation.validators.MimeTypeValidator(allowed_types=('text/plain', 'application/pdf'))])),
                ('comment', models.CharField(blank=True, default='', help_text='You can add a comment here to help you keep track of your submissions.', max_length=128)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.ComicSite')),
                ('creator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='job',
            name='method',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evaluation.Method'),
        ),
        migrations.AddField(
            model_name='job',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evaluation.Submission'),
        ),
    ]
