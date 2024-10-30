# Generated by Django 3.2.14 on 2022-07-21 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0003_remove_notification_action"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="type",
            field=models.CharField(
                choices=[
                    ("GENERIC", "Generic"),
                    ("FORUM-POST", "Forum post"),
                    ("FORUM-REPLY", "Forum post reply"),
                    ("ACCESS-REQUEST", "Access request"),
                    ("REQUEST-UPDATE", "Request update"),
                    ("NEW-ADMIN", "New admin"),
                    ("EVALUATION-STATUS", "Evaluation status update"),
                    ("MISSING-METHOD", "Missing method"),
                    ("JOB-STATUS", "Job status update"),
                    ("IMAGE-IMPORT", "Image import status update"),
                    ("FILE-COPY", "Validation failed while copying file"),
                    (
                        "CIV-VALIDATION",
                        "Component Interface Value validation failed",
                    ),
                ],
                default="GENERIC",
                help_text="Of what type is this notification?",
                max_length=20,
            ),
        ),
    ]
