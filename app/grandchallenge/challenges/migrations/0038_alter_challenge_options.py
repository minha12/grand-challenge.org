# Generated by Django 4.2.15 on 2024-09-10 13:32

from django.db import migrations


def add_add_registration_questions_permission(apps, schema_editor):

    Challenge = apps.get_model("challenges", "Challenge")  # noqa: N806
    ChallengeGroupObjectPermission = apps.get_model(  # noqa: N806
        "challenges", "ChallengeGroupObjectPermission"
    )
    Permission = apps.get_model("auth", "Permission")  # noqa: N806

    queryset = Challenge.objects.all().prefetch_related("admins_group")

    if queryset.exists():
        add_registration_question_permission = Permission.objects.get(
            codename="add_registration_question",
            content_type__app_label="challenges",
        )

        ChallengeGroupObjectPermission.objects.bulk_create(
            objs=[
                ChallengeGroupObjectPermission(
                    content_object=c,
                    group=c.admins_group,
                    permission=add_registration_question_permission,
                )
                for c in queryset.all()
            ],
            ignore_conflicts=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0037_external_evaluators_group"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="challenge",
            options={
                "ordering": ("pk",),
                "permissions": [
                    (
                        "add_registration_question",
                        "Can add registration questions",
                    )
                ],
                "verbose_name": "challenge",
                "verbose_name_plural": "challenges",
            },
        ),
        migrations.RunPython(
            add_add_registration_questions_permission, elidable=True
        ),
    ]
