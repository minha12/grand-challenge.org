# Generated by Django 3.2.12 on 2022-04-19 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0009_auto_20210831_0957"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="distribution",
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AlterField(
            model_name="product",
            name="input_data",
            field=models.CharField(max_length=300),
        ),
        migrations.AlterField(
            model_name="product",
            name="output_data",
            field=models.CharField(max_length=300),
        ),
    ]
