# Generated by Django 4.2.16 on 2024-10-23 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evaluation", "0067_remove_method_desired_gpu_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evaluation",
            name="detailed_error_message",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
