# Generated by Django 3.2.14 on 2022-07-12 12:53

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evaluation", "0027_auto_20220707_0933"),
    ]

    operations = [
        migrations.AddField(
            model_name="method",
            name="import_status",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "Initialized"),
                    (1, "Queued"),
                    (2, "Re-Queued"),
                    (3, "Started"),
                    (4, "Cancelled"),
                    (5, "Failed"),
                    (6, "Completed"),
                ],
                db_index=True,
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="method",
            name="is_in_registry",
            field=models.BooleanField(
                default=False,
                editable=False,
                help_text="Is this image in the container registry?",
            ),
        ),
        migrations.AddField(
            model_name="method",
            name="is_manifest_valid",
            field=models.BooleanField(
                default=None,
                editable=False,
                help_text="Is this image's manifest valid?",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="method",
            name="is_on_sagemaker",
            field=models.BooleanField(
                default=False,
                editable=False,
                help_text="Does a SageMaker model for this image exist?",
            ),
        ),
        migrations.AlterField(
            model_name="method",
            name="requires_cpu_cores",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("1.0"),
                max_digits=4,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="method",
            name="requires_gpu_memory_gb",
            field=models.PositiveIntegerField(default=4, null=True),
        ),
    ]
