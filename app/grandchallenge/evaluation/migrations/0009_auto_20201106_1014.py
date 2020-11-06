# Generated by Django 3.1.1 on 2020-11-06 10:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("evaluation", "0008_auto_20201103_1007"),
    ]

    operations = [
        migrations.AlterField(
            model_name="phase",
            name="evaluation_comparison_observable_url",
            field=models.URLField(
                blank=True,
                help_text="The URL of the embeddable observable notebook for comparingresults. Must be of the form https://observablehq.com/embed/@user/notebook?cell=...",
                max_length=2000,
                validators=[
                    django.core.validators.RegexValidator(
                        "^https\\:\\/\\/observablehq\\.com\\/embed\\/\\@[^\\/]+\\/[^\\?\\.]+\\?cell\\=.*$",
                        "URL must be of the form https://observablehq.com/embed/@user/notebook?cell=*",
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="phase",
            name="evaluation_detail_observable_url",
            field=models.URLField(
                blank=True,
                help_text="The URL of the embeddable observable notebook for viewing individual results. Must be of the form https://observablehq.com/embed/@user/notebook?cell=...",
                max_length=2000,
                validators=[
                    django.core.validators.RegexValidator(
                        "^https\\:\\/\\/observablehq\\.com\\/embed\\/\\@[^\\/]+\\/[^\\?\\.]+\\?cell\\=.*$",
                        "URL must be of the form https://observablehq.com/embed/@user/notebook?cell=*",
                    )
                ],
            ),
        ),
    ]
