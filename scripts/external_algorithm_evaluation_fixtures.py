from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from faker import Faker
from knox.models import AuthToken, hash_token
from knox.settings import CONSTANTS

from grandchallenge.challenges.models import Challenge
from grandchallenge.components.models import ComponentInterface
from grandchallenge.evaluation.models import Phase
from grandchallenge.evaluation.utils import SubmissionKindChoices
from grandchallenge.verifications.models import Verification
from scripts.algorithm_evaluation_fixtures import (
    _create_algorithm,
    _create_archive,
    _create_challenge,
    _get_inputs,
    _get_outputs,
    _get_users,
)
from grandchallenge.algorithms.models import AlgorithmImage # Keep this import


def run():
    print("👷 Creating External Algorithm Evaluation Fixtures")

    evaluator = _get_or_create_evaluator()

    users = _get_users()
    inputs = []  # Convert QuerySet to list
    outputs = _get_outputs()
    
    # Add new custom interfaces
    custom_interfaces = create_custom_interfaces()
    inputs.extend(custom_interfaces)  # Now this will work with a list

    challenge_count = Challenge.objects.count()
    archive = _create_archive(
        creator=users["demo"],
        interfaces=inputs,
        suffix=challenge_count,
        items=1,
    )
    challenge = _create_challenge(
        creator=users["demo"],
        participant=users["demop"],
        archive=archive,
        suffix=challenge_count,
        inputs=inputs,
        outputs=outputs,
    )
    
    # Capture the algorithm and algorithm_image instances
    _create_algorithm(
        creator=users["demop"],
        inputs=inputs,
        outputs=outputs,
        suffix=f"Image {challenge_count}",
    )
    _create_external_evaluation_phase(
        evaluator=evaluator,
        challenge=challenge,
        inputs=inputs,
        outputs=outputs,
    )


def _create_external_evaluation_phase(
    *, evaluator, challenge, inputs, outputs
):
    challenge.external_evaluators_group.user_set.add(evaluator)

    existing_phase = challenge.phase_set.get()

    p = Phase.objects.create(challenge=challenge, title="Phase 2")

    p.algorithm_inputs.set(inputs)
    p.algorithm_outputs.set(outputs)

    p.title = "External Algorithm Evaluation"
    p.submission_kind = SubmissionKindChoices.ALGORITHM
    # p.parent = existing_phase
    p.external_evaluation = True
    p.score_jsonpath = "score"
    p.submissions_limit_per_user_per_period = 10
    p.save()


def _get_or_create_evaluator():
    username = "evaluator"
    fake = Faker()

    user, created = get_user_model().objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@example.com",
            "is_active": True,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
        },
    )

    if not created:
        return user

    user.set_unusable_password()
    user.save()

    EmailAddress.objects.create(
        user=user,
        email=user.email,
        verified=True,
        primary=True,
    )

    Verification.objects.create(
        user=user,
        email=user.email,
        is_verified=True,
    )

    user.user_profile.institution = fake.company()
    user.user_profile.department = f"Department of {fake.job().title()}s"
    user.user_profile.country = fake.country_code()
    user.user_profile.receive_newsletter = False
    user.user_profile.save()

    token = "033608db32513e3ff28ac08ffa228fb414d718910397ce3670c339fe126ad7b6"

    AuthToken(
        token_key=token[: CONSTANTS.TOKEN_KEY_LENGTH],
        key=hash_token(token),
        user=user,
        expiry=None,
    ).save()

    return user


def create_custom_interfaces():
    from grandchallenge.components.models import ComponentInterface
    
    # First try to get interfaces by slug if they exist
    interfaces = []
    
    # Try to get HE Staining interface
    try:
        he_staining = ComponentInterface.objects.get(slug="he-staining")
        interfaces.append(he_staining)
    except ComponentInterface.DoesNotExist:
        # Create it if it doesn't exist
        he_staining = ComponentInterface.objects.create(
            title="HE Staining",
            kind=ComponentInterface.Kind.IMAGE,
            relative_path=f"images/he-staining"  # Make unique
        )
        interfaces.append(he_staining)
    
    # Try to get Tissue Mask interface
    try:
        tissue_mask = ComponentInterface.objects.get(slug="tissue-mask")
        interfaces.append(tissue_mask)
    except ComponentInterface.DoesNotExist:
        # Create it if it doesn't exist
        tissue_mask = ComponentInterface.objects.create(
            title="Tissue Mask",
            kind=ComponentInterface.Kind.IMAGE,
            relative_path=f"images/tissue-mask"  # Make unique
        )
        interfaces.append(tissue_mask)
    
    return interfaces
