# Generated by Django 4.2.16 on 2024-10-10 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evaluation", "0064_evaluation_requires_gpu_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="phase",
            name="evaluation_requires_gpu_type",
            field=models.CharField(
                choices=[
                    ("", "No GPU"),
                    ("A100", "NVIDIA A100 Tensor Core GPU"),
                    ("A10G", "NVIDIA A10G Tensor Core GPU"),
                    ("V100", "NVIDIA V100 Tensor Core GPU"),
                    ("K80", "NVIDIA K80 GPU"),
                    ("T4", "NVIDIA T4 Tensor Core GPU"),
                ],
                default="",
                blank=True,
                help_text="What GPU to attach to this phases evaluations. Note that the GPU attached to any algorithm inference jobs is determined by the submitted algorithm.",
                max_length=4,
            ),
        ),
        migrations.AddField(
            model_name="phase",
            name="evaluation_requires_memory_gb",
            field=models.PositiveSmallIntegerField(
                default=8,
                help_text="How much memory to assign to this phases evaluations. Note that the memory assigned to any algorithm inference jobs is determined by the submitted algorithm.",
            ),
        ),
    ]
