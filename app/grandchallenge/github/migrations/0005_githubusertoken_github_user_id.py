# Generated by Django 3.1.13 on 2021-09-20 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("github", "0004_auto_20210916_0746"),
    ]

    operations = [
        migrations.AddField(
            model_name="githubusertoken",
            name="github_user_id",
            field=models.BigIntegerField(null=True),
        ),
    ]
