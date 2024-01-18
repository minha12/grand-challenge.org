# Generated by Django 4.2.8 on 2024-01-16 13:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workstation_configs", "0023_workstationconfig_ghosting_slice_depth"),
    ]

    operations = [
        migrations.AddField(
            model_name="workstationconfig",
            name="default_annotation_line_width",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Default line width in pixels for displaying and creating annotations",
                null=True,
            ),
        ),
    ]
