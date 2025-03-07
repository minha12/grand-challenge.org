import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings

from grandchallenge.core.storage import public_s3_storage


def run():
    """Sets up the permissions on the minio buckets"""
    print("🔐 Setting up minio 🔐")

    if not settings.DEBUG:
        raise RuntimeError(
            "Skipping this command, server is not in DEBUG mode."
        )

    _setup_public_storage()
    _setup_components_storage()

    print("✨ Minio set up ✨")


def _setup_public_storage():
    """
    Add anonymous read only to public S3 storage.

    Only used in development. In production, set a similar policy on the S3 bucket.
    """
    host_alias = "local"
    policy_name = "public_read"
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{public_s3_storage.bucket_name}/*",
            }
        ],
    }

    subprocess.check_call(
        [
            "mc",
            "config",
            "host",
            "add",
            host_alias,
            settings.AWS_S3_ENDPOINT_URL,
            os.environ["AWS_ACCESS_KEY_ID"],
            os.environ["AWS_SECRET_ACCESS_KEY"],
        ]
    )

    with TemporaryDirectory() as tmp_dir:
        policy_file = Path(tmp_dir) / f"{policy_name}.json"

        with open(policy_file, "w") as f:
            f.write(json.dumps(policy))

        subprocess.check_call(
            [
                "mc",
                "anonymous",
                "set-json",
                str(policy_file),
                f"{host_alias}/{public_s3_storage.bucket_name}",
            ]
        )


def attach_policy(host_alias, policy_name, user):
    result = subprocess.run(
        [
            "mc",
            "admin",
            "policy",
            "attach",
            host_alias,
            policy_name,
            "--user",
            user,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        error_message = result.stderr.strip()
        if "The specified policy change is already in effect" in error_message:
            print(f"Policy '{policy_name}' is already attached to user '{user}'. Continuing...")
        else:
            print(f"Error attaching policy '{policy_name}' to user '{user}': {error_message}")
            sys.exit(1)
    else:
        print(f"Policy '{policy_name}' attached to user '{user}' successfully.")


def _setup_components_storage():
    """
    Add a user and IAM role for the components storage

    Only used in development. In production, create similar policies and roles.
    """
    host_alias = "local"
    policy_name = "components"
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": ["s3:GetObject"],
                "Effect": "Allow",
                "Resource": [
                    f"arn:aws:s3:::{settings.COMPONENTS_INPUT_BUCKET_NAME}/*"
                ],
                "Sid": "GetInputs",
            },
            {
                "Action": ["s3:PutObject"],
                "Effect": "Allow",
                "Resource": [
                    f"arn:aws:s3:::{settings.COMPONENTS_OUTPUT_BUCKET_NAME}/*"
                ],
                "Sid": "PutOutputs",
            },
        ],
    }

    subprocess.check_call(
        [
            "mc",
            "config",
            "host",
            "add",
            host_alias,
            settings.AWS_S3_ENDPOINT_URL,
            os.environ["AWS_ACCESS_KEY_ID"],
            os.environ["AWS_SECRET_ACCESS_KEY"],
        ]
    )

    with TemporaryDirectory() as tmp_dir:
        policy_file = Path(tmp_dir) / f"{policy_name}.json"
        with open(policy_file, "w") as f:
            f.write(json.dumps(policy))
        subprocess.check_call(
            [
                "mc",
                "admin",
                "policy",
                "create",
                host_alias,
                policy_name,
                str(policy_file),
            ]
        )

    # Add user
    subprocess.check_call(
        [
            "mc",
            "admin",
            "user",
            "add",
            host_alias,
            settings.COMPONENTS_DOCKER_TASK_AWS_ACCESS_KEY_ID,
            settings.COMPONENTS_DOCKER_TASK_AWS_SECRET_ACCESS_KEY,
        ]
    )

    # Attach the policy to the user using the helper function
    attach_policy(
        host_alias,
        policy_name,
        settings.COMPONENTS_DOCKER_TASK_AWS_ACCESS_KEY_ID,
    )

    # Attach the policy to 'componentstask' user using the helper function
    attach_policy(
        "local",
        "components",
        "componentstask",
    )
