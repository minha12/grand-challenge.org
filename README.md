# grand-challenge.org

## Algorithm Submissions and API Usage

To create algorithm submissions, you need a verified account. You can apply for verification in your profile settings, where you can also create your API token for accessing the API. For more information, see:
* [API Documentation](https://grand-challenge.org/documentation/grand-challenge-api/)
* [Python Client (gcapi)](https://pypi.org/project/gcapi/)

We provide an Apache Airflow module that implements all the API calls as a barebone example implementation.

## Local Development Setup

To use a local instance of Grand Challenge, follow these steps:

1. Spin up a local instance following the [development guide](https://github.com/comic/grand-challenge.org/blob/main/app/docs/development.rst)

2. Create a test environment with a claimable evaluation:
   ```bash
   # Create a dummy challenge with external evaluation
   make external_algorithm_evaluation_fixtures

   # Create a superuser (will output login tokens)
   make superuser
   ```

3. Configure user permissions:
   * Sign in as superuser at your local instance
   * Go to the database admin (https://gc.localhost/django-admin/auth/group/)
   * Select `algorithm-evaluation-1_external_evaluators` and add a user (e.g., demo)

4. Setup for evaluation:
   * Sign in as demo user (password: demo)
   * Create an API token in profile settings
   * Use this token with the Apache Airflow module to access claimable evaluations

To create a claimable evaluation:
1. Log in as demo
2. Go to the challenge
3. Submit to the Algorithm Evaluation phase
4. Once completed, submit to the External Algorithm Evaluation phase
The submission will appear in the list of claimable evaluations, including the submitter's username.
