# Generated by Django 3.1.11 on 2021-06-01 08:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("organizations", "0002_auto_20210512_1437"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="editors_group",
            field=models.OneToOneField(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="editors_of_organization",
                to="auth.group",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="members_group",
            field=models.OneToOneField(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="members_of_organization",
                to="auth.group",
            ),
        ),
    ]
