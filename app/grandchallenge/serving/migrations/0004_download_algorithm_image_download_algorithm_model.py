# Generated by Django 4.2.14 on 2024-08-26 15:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("algorithms", "0054_alter_algorithmimage_options_and_more"),
        (
            "serving",
            "0003_alter_download_unique_together_remove_download_count",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="download",
            name="algorithm_image",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="algorithms.algorithmimage",
            ),
        ),
        migrations.AddField(
            model_name="download",
            name="algorithm_model",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="algorithms.algorithmmodel",
            ),
        ),
    ]
