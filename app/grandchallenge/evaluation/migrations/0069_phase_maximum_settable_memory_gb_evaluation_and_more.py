# Generated by Django 4.2.16 on 2024-11-21 12:39

from django.db import migrations, models

import grandchallenge.components.schemas
import grandchallenge.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("evaluation", "0068_alter_evaluation_detailed_error_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="phase",
            name="evaluation_maximum_settable_memory_gb",
            field=models.PositiveSmallIntegerField(
                default=32,
                help_text="Maximum amount of memory that challenge admins will be able to assign for the evaluation method.",
            ),
        ),
        migrations.AddField(
            model_name="phase",
            name="evaluation_selectable_gpu_type_choices",
            field=models.JSONField(
                default=grandchallenge.components.schemas.get_default_gpu_type_choices,
                help_text='The GPU type choices that challenge admins will be able to set for the evaluation method. Options are ["", "A100", "A10G", "V100", "K80", "T4"].',
                validators=[
                    grandchallenge.core.validators.JSONValidator(
                        schema={
                            "$schema": "http://json-schema.org/draft-07/schema",
                            "items": {
                                "enum": [
                                    "",
                                    "A100",
                                    "A10G",
                                    "V100",
                                    "K80",
                                    "T4",
                                ],
                                "type": "string",
                            },
                            "title": "The Selectable GPU Types Schema",
                            "type": "array",
                            "uniqueItems": True,
                        }
                    )
                ],
            ),
        ),
    ]
