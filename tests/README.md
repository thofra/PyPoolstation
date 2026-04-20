# Running Tests

This directory contains basic tests for the `PyPoolstation` library.

## Prerequisites

Before running the tests, you need to configure your credentials.

1.  Create a file named `credentials.json` in the root directory of the project (parent of this `tests` directory).
2.  Add your Poolstation username and password to the file in JSON format:

```json
{
    "username": "your_email@example.com",
    "password": "your_password",
    "login_code": ""
}
```

> **Note:** The `credentials.json` file is ignored by git to protect your sensitive information. If your account triggers 2FA authentication, wait for the email containing the code, place it inside the `login_code` field, and run the test again.

## Running the Tests

You can run automated integration tests against real hardware using the built-in python `unittest` module:

```bash
# Using the virtual environment python
venv\Scripts\python -m unittest tests.test_integration

# Or if activated:
python -m unittest tests.test_integration
```

## Running the Basic Test Script

To run the exploratory test script, execute the following command from the root of the project:

```bash
# Using the virtual environment python
venv\Scripts\python tests/test_basic.py
```

Or if you have your environment activated:

```bash
python tests/test_basic.py
```

This script will:
1.  Authenticate using the provided credentials.
2.  Fetch all available pools.
3.  Sync and print the details of the first pool found, including UV status and relay information.
