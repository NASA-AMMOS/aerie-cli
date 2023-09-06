# Aerie-CLI

Aerie-CLI provides a command-line interface and user-extendable Python API for interacting with an instance of Aerie.

> Note: this project is an informal CLI and is _not_ maintained by the MPSA Aerie team.

## Getting Started

This short procedure will get you up and running with the basics of the CLI. Read the following sections for more information.

1. Install/update to Python >= 3.6

2. Install Aerie-CLI from Github:

   ```sh
   ➜  python3 -m pip install git+https://github.com/NASA-AMMOS/aerie-cli.git@main
   ```

3. Configure access to an Aerie host

   1. If you've been provided a Configuration JSON, reference that file

   2. If you don't have already have a Configuration JSON, copy the following to a JSON file for a local Aerie deployment (replacing the username with your own):

      ```json
      [
        {
          "name": "localhost",
          "graphql_url": "http://localhost:8080/v1/graphql",
          "gateway_url": "http://localhost:9000",
          "username": "my_username"
        }
      ]
      ```

   3. Load either your given configuration(s) or the configuration above into Aerie-CLI:

      ```sh
      ➜  aerie-cli configurations load -i JSON_FILE
      ```

4. Activate a configuration to start a session with an Aerie host:

   ```sh
   ➜  aerie-cli activate
   1) localhost
   Select an option: 1
   ```

5. Try out a command to list the plans in Aerie:

   ```sh
   ➜  aerie-cli plans list
   ```

6. Use the `--help` flag on any command to see available subcommands and parameters. For example:

   ```sh
   ➜  aerie-cli --help
   ...
   ➜  aerie-cli plans --help
   ...
   ➜  aerie-cli plans download --help
   ```

---

## CLI Usage

### Setup

Aerie-CLI uses configurations to define different Aerie hosts. Define configurations by either loading JSON configurations or manually via the CLI. Configurations persist on a per-user basis and may be shared between installations.

#### Defining Hosts with a Configuration File

If you have a file of configurations to load, you can simply use the `configurations load` command:

```sh
➜  aerie-cli configurations load -i PATH_TO_JSON
```

You can view the configurations you've loaded with the `configurations list` command:

```sh
➜  aerie-cli configurations list
Configuration file location: /Users/<username>/Library/Application Support/aerie_cli/config.json

                                         Aerie Host Configurations
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Host Name ┃ GraphQL API URL                  ┃ Aerie Gateway URL     ┃ Username ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ localhost │ http://localhost:8080/v1/graphql │ http://localhost:9000 │          │
└───────────┴──────────────────────────────────┴───────────────────────┴──────────┘
```

#### Defining hosts via the CLI

If you haven't been provided a JSON configuration for a host, you can create a configuration by running `aerie-cli configurations create` and follow the prompts. 

### Sessions and Roles

Aerie-CLI maintains a persistent "session" with an Aerie instance so multiple commands can run without needing to re-authenticate. To start a session, use the `activate` command:

```sh
➜  aerie-cli activate
    1) localhost
    ...
    Select an option: 1
```

Aerie uses "roles" to adjust what a client is permitted to do. To view the active configuration name and current role, use the `status` command:

```sh
➜  aerie-cli status
Active configuration: localhost
Active role: viewer
```

The default role is configured by Aerie. To change the selected role for the active Aerie-CLI session, use the `role` command:

```sh
➜  aerie-cli role
Active Role: viewer
	1) aerie_admin
	2) user
	3) viewer
Select an option: 1
Changed role to: aerie_admin
```

At any time, the active session can be closed with the `deactivate` command.

### Commands

Commands are the main functions available via the CLI and are broken down into several levels. For example, the top-level `plans` command has sub-commands for `list`, `upload`, `simulate`, and more. From any command or sub-command, use the `--help` flag to learn about what commands are available or what arguments are required.

Help at script level:

```sh
➜  aerie-cli --help
```

Help at command level:

```sh
➜  aerie-cli plans --help
```

Help at sub-command level:

```sh
➜  aerie-cli plans download --help
```

#### Interactive vs. Non-Interactive

If a command is invoked without the necessary arugments, interactive prompts are provided:

```sh
>>> aerie-cli plans download
> Id: 42
> Output: sample-output.json
```

Alternatively, arguments can be provided using flags:

```sh
>>> aerie-cli plans download --id 42 --output sample-output.json
```

### Advanced Topics

#### Configuring for External Authentication

Aerie-CLI configurations include a mechanism to authenticate against an external authentication service which may require additional credentials as cookies for accessing Aerie. Aerie-CLI will issue a post request with given JSON data to a provided authentication endpoint and persist any returned cookies in a browser-like manner for the remainder of the Aerie-CLI session.

An external authentication service is configured using the key `external_auth` in the JSON configuration file as follows:

```json

  {
    "name": "my_host",
    "graphql_url": "https://hostname/v1/graphql",
    "gateway_url": "https://hostname/gateway",
    "username": "my_username",
    "external_auth": {
      "auth_url": "https://auth_service/route",
      "static_post_vars": {
        "username": "my_username"
      },
      "secret_post_vars": [
        "password"
      ]
    }
  }
```

Here, `static_post_vars` is an object containing fixed values to include in the post request payload such as usernames and other persistent, non-sensitive fields. `secret_post_vars` is a list of keys for credentials which may be sensitive or time-varying. The user will be prompted to provide the "secret" values using hidden entry in the terminal when activating a session with external authentication.

In this example, the user would be prompted to enter a value for "password" and, assuming they enter "my_password", the post request JSON would include the following:

```json
{
  "username": "my_username",
  "password": "my_password"
}
```

#### Using a Hasura Admin Secret

In some cases, an admin secret may be used to permit otherwise prohibited requests through Hasura (the software behind the Aerie API). When running a command, the user may add the `--hasura-admin-secret` flag after the `aerie-cli` command to use these elevated privileges for the following command. 

---

## Python API

### Quickstart Guide

Instead of using the CLI for interactive use cases, the underlying classes and methods behind Aerie-CLI can be invoked directly in Python scripts.

The key constructs are:

- `aerie_cli.aerie_host.AerieHost`: An abstraction for an Aerie Host, including methods for authentication and issuing requests to the Aerie API.
- `aerie_cli.aerie_client.AerieClient`: A class containing common requests and reusable logic to interact with data in Aerie. 

The following example defines an `AerieHost` using the necessary URLs, authenticates with a command-line prompt for the user's password, and issues a simple request using one of the built-in requests.

```py
from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AerieHost

from getpass import getpass

# These URLs define the Aerie host
GRAPHQL_URL = "http://myhostname:8080/v1/graphql"
GATEWAY_URL = "http://myhostname:9000"

# User credentials. The password may be omitted on Aerie instances with authentication disabled
USERNAME = "myusername"
PASSWORD = getpass(prompt='Password: ')

# Define the Aerie host and provide user credentials
aerie_host = AerieHost(GRAPHQL_URL, GATEWAY_URL)
aerie_host.authenticate(USERNAME, PASSWORD)

# AerieClient takes in a host and returns an object to issue requests to that host
client = AerieClient(aerie_host)

# Simple example of a request to get an activity plan using the plan ID
plan = client.get_activity_plan_by_id(42)
print(plan.name)
```

Look through the available methods in the provided `AerieClient` class to find ones that suit your needs.

### Adding Methods

If you need to write a custom query, you can extend the `AerieClient` class and add your own method. Access the Aerie host using the `aerie_host` property. For example:

```py

# ...

class MyCustomAerieClient(AerieClient):
    def get_plan_id_by_name(self, plan_name: str) -> int:
        my_query = """
        query GetPlanIdByName($plan_name: String!) {
            plan(where: { name: { _eq: $plan_name } }) {
                id
            }
        }
        """

        # Pass variables for the query as keyword arguments
        resp = self.aerie_host.post_to_graphql(
            my_query,
            plan_name=plan_name
        )
        return resp[0]["id"]
```

Now, you can use your custom method like any other:

```py
# ...
client = MyCustomAerieClient(aerie_host)
plan_id = client.get_plan_id_by_name("my-plan-name")
print(plan_id)
```

### Using the Active CLI Session

If your application will be run by a user who may also be using the CLI, you may reduce the amount of code required to configure an Aerie host and instead just use the active session. Aerie-CLI provides a utility to retrieve an `AerieClient` instance from the active CLI session:

```py
from aerie_cli.utils.sessions import get_active_session_client

# client is an instance of `AerieClient`
client = get_active_session_client()

# Issue requests like normal
plan = client.get_activity_plan_by_id(...)
```

### Advanced Authentication

If you have needs for authentication (e.g., a custom token system) that aren't provided by Aerie-CLI, you can use any features supported by the [Python `requests`](https://requests.readthedocs.io/en/latest/) module's [`Session` class](https://requests.readthedocs.io/en/latest/api/#request-sessions). Instantiate a session object, manipulate/add headers/cookies/SSL certificates/etc. as necessary, and use to instantiate an `AerieHostSession`:

```py
# ...
from requests import Session

my_custom_requests_session = Session()
# Manipulate as necessary
# ...

aerie_host = AerieHost(
    GRAPHQL_URL,
    GATEWAY_URL,
    session=my_custom_requests_session
)
aerie_host.authenticate(...)
client = AerieClient(aerie_host)

# Use client as normal
```

---

## Contributing

### Contributor Installation

If you'd like to contribute to this project, you'll first need to clone this repository, and you will have to install [`poetry`](https://python-poetry.org/docs/master/).

Then, you will need to run the following commands:

1. `poetry install` -- installs the necessary dependencies into a poetry-managed virtual environment.
2. ~`poetry run pre-commit install` -- creates a git [pre-commit](https://pre-commit.com) hook which will automatically run formatters, style checks, etc. against your proposed commits.~

To run commands from source as you edit, use the `poetry run` command. For example:

```
poetry run aerie-cli plans simulate --id 42
```

<!-- ### Deployment

To deploy a new version of aerie-cli:

- Verify the version number in `pyproject.toml` is incremented from the current version in PyPI
- Clear out any previous build artifacts, if present, from the root of the repository:
  ```sh
  rm -rf dist/
  ```
- Build the project using Poetry:
  ```sh
  poetry build
  ```

To upload to PyPI, use twine:

```sh
python3 -m twine upload dist/*
```

Details can be found in the [twine documentation](https://twine.readthedocs.io/en/stable/index.html). -->

### Pre-Commit Hook

Whenever you try to commit your changes (`git commit -m "my commit message"`), you may experience errors if your current shell doesn't have access to the dependencies required for the pre-commit hook. To remedy this, simply prefix your `git` command with `poetry run`. E.g.: `poetry run git commit -m "my commit message"`.

If your code does not conform to formatting or style conventions, your commit will fail, and you will have to revise your code before committing it. Note, however, that our auto-formatter `black` does modify your files in-place when you run the pre-commit hook; you'll simply have to `git add` the changed files to stage the formatting changes, and you can attempt to commit again.

### Dependency Management

If you'd like to add or remove dependencies, you can use the `poetry add` and `poetry remove` commands, respectively. These will install the dependencies in your `poetry`-managed virtual environment, update your `pyproject.toml` file, and update your `poetry.lock` file. If you update the dependencies, you should stage and commit your changes to these two files so that others will be guaranteed to have the same Python configuration.

For more information on dependency and project management, see the [`poetry` docs](https://python-poetry.org/docs/master/).

### Testing

Aerie-CLI has unit tests and integration tests built with the [pytest](https://docs.pytest.org/) library.

#### Unit Tests

Unit tests can be run anytime from `tests/unit_tests` and reference local test files. `test_aerie_client.py` is where unit tests are added to exercise particular methods of the `AerieClient` class using mocked Aerie API responses. 

Run the unit tests using `pytest`:

```
cd tests
poetry run pytest unit_tests
```

#### Integration Tests

A separate suite of tests is designed to validate CLI functionality against a local instance of Aerie. See the [integration testing documentation](tests/integration_tests/README.md) for details.

The integration tests are based on `Typer` testing documentation found [here](https://typer.tiangolo.com/tutorial/testing/).

### IDE Settings

Since you are using `poetry` for development, your system Python interpreter will likely complain about any dependencies used within this project. To remedy this, you'll need to select the Python interpreter from your `poetry` virtualenv in your IDE. The method for doing so is unfortunately IDE-dependent, however.

#### VS Code

For Mac users developing in VS Code, you can achieve this by adding the following setting to your `settings.json` file:

```
"python.venvPath": "~/Library/Caches/pypoetry/virtualenvs",
```

After doing this, you can select a new Python interpreter by typing `Cmd + Shift + P` and selecting a Python interpreter which corresponds to your `poetry` virtualenv:

<img width="601" alt="image" src="https://user-images.githubusercontent.com/7908658/201275707-00caca06-5e2b-4258-b5c4-f0548134af2f.png">
