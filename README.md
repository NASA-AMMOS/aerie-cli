# Aerie CLI

Note: this project is an informal CLI and is _not_ maintained by the MPSA Aerie team.

##### Table of Contents

- [Aerie CLI](#aerie-cli) - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Getting Started](#getting-started)
  - [Installation](#installation)
    - [Installation with `pip`](#installation-with-pip)
    - [Updating with `pip`](#updating-with-pip)
    - [Installation with `poetry`](#installation-with-poetry)
  - [Usage](#usage)
    - [Setup](#setup)
      - [With a Configuration File](#with-a-configuration-file)
      - [Via the CLI](#via-the-cli)
      - [Handling Authentication](#handling-authentication)
    - [Commands](#commands)
      - [Interactive](#interactive)
      - [Non-Interactive](#non-interactive)
      - [Help](#help)
      - [Specific Sub-Commands: Plans](#specific-sub-commands-plans)
        - [Download](#download)
        - [Upload](#upload)
        - [Duplication](#duplication)
        - [Simulation](#simulation)
      - [Specific Sub-Commands: Models](#specific-sub-commands-models)
        - [Upload](#upload-1)
        - [List](#list)
        - [Delete](#delete)
        - [Clean](#clean)
    - [Python API](#python-api)
      - [Basic Usage](#basic-usage)
      - [Adding Methods](#adding-methods)
      - [Advanced Authentication](#advanced-authentication)
  - [Contributing](#contributing)
    - [Contributor Installation](#contributor-installation)
    - [Deployment](#deployment)
    - [Dependency Management](#dependency-management)
    - [Testing](#testing)
      - [Unit Tests](#unit-tests)
    - [Pre-Commit Hook](#pre-commit-hook)
    - [IDE Settings](#ide-settings)
      - [VS Code](#vs-code)

---

## Overview

Aerie CLI provides a command-line interface and user-extendable Python backend for interacting with an instance of Aerie.

---

## Getting Started

This short procedure will get you up and running with the basics of Aerie CLI. Read the following sections for more information.

1. Install/update to Python 3.9

2. Install Aerie CLI from Github:

   ```sh
   python3 -m pip install git+https://github.com/NASA-AMMOS/aerie-cli.git#main
   ```

3. Configure access to an Aerie host

   1. If you've been provided a Configuration JSON, reference that file

   2. If you don't have already have a Configuration JSON, copy the following to a JSON file for a local Aerie deployment:

      ```json
      {
        "name": "localhost",
        "graphql_url": "http://localhost:8080/v1/graphql",
        "gateway_url": "http://localhost:9000",
        "auth_method": "None"
      }
      ```

   3. Load either your given configuration(s) or the configuration above into Aerie CLI:

      ```sh
      aerie-cli configurations load -i JSON_FILE
      ```

4. Activate a configuration to start communicating with an Aerie host:

   ```sh
   ➜  tools aerie-cli configurations activate
   1) localhost
   Select an option: 1
   ```

5. Try out a command to list the plans in Aerie:

   ```sh
   aerie-cli plans list
   ```

6. Use the `--help` flag on any command to see available subcommands and parameters. For example:

   ```sh
   aerie-cli --help
   ...
   aerie-cli plans --help
   ...
   aerie-cli plans download --help
   ```

---

## Installation

### Installation with `pip`

First, ensure that **`Python 3.9`** is installed on your local machine as the CLI will is not compatible with older versions. Once `Python 3.9` has been installed, you can install `aerie-cli` with the following command:

```sh
python3 -m pip install git+https://github.com/NASA-AMMOS/aerie-cli.git#main
```

If you want to install from a specific branch of `aerie-cli` replace `#main` in the GitHub url with `@branchname` as following:

```sh
$ python3 -m pip install git+https://github.com/NASA-AMMOS/aerie-cli.git@branchname
```

You can confirm that `aerie-cli` has been installed on your system:

```sh
>>> which aerie-cli
> path/to/aerie-cli
```

### Updating with `pip`

In order to update your currently installed version of `aerie-cli`, first uninstall your local package and then reinstall from GitHub.

```sh
$ python3 -m pip uninstall aerie_cli
> Successfully uninstalled aerie-cli-<version>
```

### Installation with `poetry`

If you use `poetry` for your dependency management and intend to use this package in another Python project, you can install this package to an existing `poetry` project with:

```sh
poetry add git+https://github.com/NASA-AMMOS/aerie-cli.git#main
```

For more info on `poetry`, see the [Contributing](#contributing) section below.

---

## Usage

### Setup

Aerie CLI uses configurations to define different Aerie hosts. Define configurations by either loading JSON configurations or manually via the CLI.

#### With a Configuration File

If you have a file of configurations to load, you can simply use the `configurations load` command:

```sh
➜  aerie-cli configurations load -i PATH_TO_JSON
```

You can view the configurations you've loaded with the `configurations list` command:

```sh
➜  aerie-cli configurations list
Configuration file location: /Users/<username>/Library/Application Support/aerie_cli/config.json

                                         Aerie Host Configurations
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Host Name ┃ GraphQL API URL                  ┃ Aerie Gateway URL     ┃ Authentication Method ┃ Username ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ localhost │ http://localhost:8080/v1/graphql │ http://localhost:9000 │ None                  │          │
└───────────┴──────────────────────────────────┴───────────────────────┴───────────────────────┴──────────┘
```

#### Via the CLI

If you haven't been provided a JSON configuration for a host, you can create a configuration by running `aerie-cli configurations create` and follow the prompts. For example, to configure localhost:

```sh
➜  aerie-cli configurations create
   Name: localhost
   GraphQL URL: http://localhost:8080/v1/graphql
   Gateway URL: http://localhost:9000
   Authentication method (None, Native, Cookie) [None]: None
```

To view available configurations, use `aerie-cli configurations list`:

```sh
➜  aerie-cli configurations list
Configuration file location: /Users/<username>/Library/Application Support/aerie_cli/config.json

                                         Aerie Host Configurations
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Host Name ┃ GraphQL API URL                  ┃ Aerie Gateway URL     ┃ Authentication Method ┃ Username ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ localhost │ http://localhost:8080/v1/graphql │ http://localhost:9000 │ None                  │          │
└───────────┴──────────────────────────────────┴───────────────────────┴───────────────────────┴──────────┘
```

#### Handling Authentication

Each configuration must specify an authentication method, which depends on how the Aerie instance is deployed. Aerie CLI provides three ways to authenticate with an Aerie host:

| Method   | Description                                                     |
| :------- | :-------------------------------------------------------------- |
| `None`   | No authentication (e.g., for a local deployment)                |
| `Native` | Default Aerie authentication scheme (Token-based)               |
| `Cookie` | Cookie-based authentication (used on some advanced deployments) |

### Commands

Begin by activating a configuration. This will store a persistent session with an Aerie host that will be used for all CLI commands.

```sh
aerie-cli configurations activate
    1) localhost
    ...
    Select an option: 1
```

We're using the [`typer`](https://typer.tiangolo.com) library for command-line input. This allows us to run any of these commands interactively (with user prompts for each un-provided argument) OR non-interactively (where all are provided).

Currently, Aerie-CLI supports `plans`, `models`, and `expansion` command trees.

**Note**: during the early stages of development, the examples in this README may not be perfectly in sync with updates to the commands and sub-commands supported by the CLI. If there is any discrepancy, you're encouraged to use the `--help` option (see [Help](#help) section) for information on commands and sub-commands in your specific CLI version.

#### Interactive

For example, we can run a script without any CLI args/options, and we'll be prompted for the necessary information:

```sh
>>> aerie-cli plans download
> Id: 42
> Output: sample-output.json
```

#### Non-Interactive

Alternatively, if we get tired of repeatedly providing the same inputs (or want to build automation on top of our CLI), we can provide the arguments directly as we invoke the CLI:

```sh
>>> aerie-cli plans download --id 42 --output sample-output.json
```

NOTE: you are **not** encouraged to provide your password in plaintext as an input to the script upon invocation; it will prompt you for it in your shell and hide your input. It may be provided at the command-line, however, if you're using an automation tool like Jenkins which is capable of auto-credential-hiding in logs.

#### Help

You can also use `--help` liberally to get more info at various stages in the process:

E.g.:

Help at script level:

```sh
>>> aerie-cli --help
Usage: aerie-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  plans
  models
  expansion
```

Help at command level:

```sh
>>> aerie-cli plans --help
Usage: aerie-cli plans [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  download   Download a plan and save it locally as a JSON file.
  duplicate  Duplicate an existing plan.
  simulate   Download a plan and save it locally as a JSON file.
  upload     Create a plan from an input JSON file.
```

Help at sub-command level:

```sh
>>> aerie-cli plans download --help
Usage: aerie-cli plans download [OPTIONS]

  Download a plan and save it locally as a JSON file

Options:
  --id INTEGER       Plan ID  [required]
  --output TEXT      The output file destination  [required]
  --help             Show this message and exit.
```

#### Specific Sub-Commands: Plans

##### Download

You can download an Aerie plan simply as such:

```sh
aerie-cli plans download
```

The output JSON file resembles the plan as hosted on the Aerie deployment.

##### Upload

You can upload an Aerie plan simply with:

```sh
aerie-cli plans upload
```

NOTE: a downloaded JSON plan includes arguments for `id` (plan ID), `model_id` (mission model / adaptation ID), and an `id` for each activity instance. These are included for the convenience of the user, but if the same downloaded plan is used for upload, these fields are ignored (since new activity instances and a new plan container are created for an upload). You may feel free to delete these fields from persisted plans if you'd like.

##### Duplication

You can duplicate an Aerie plan (create a copy against the same mission model) with:

```sh
aerie-cli plans duplicate
```

##### Simulation

You can simulate an Aerie plan with:

```sh
aerie-cli plans simulate
```

If an `--output` argument isn't provided, this will simply run a simulation so that the results are cached on the server and are quickly visible in the UI. However, if you want to persist the results in JSON form, you should provide an `--output` path to a local file.

#### Specific Sub-Commands: Models

##### Upload

You can upload an Aerie mission model simply as such:

```sh
aerie-cli models upload
```

NOTE: Required fields include `mission-model-path`, `model-name`, and `mission-name`. The model version defaults to an empty string that can be overwritten by the user input. Alternatively, use the `--time-tag-version` flag to set the model version with the current timestamp.

##### List

You can list out all current Aerie mission models like so:

```sh
aerie-cli models list
```

##### Delete

You can delete an Aerie model simply with:

```sh
aerie-cli models delete
```

NOTE: Required fields include `model-id`.

##### Clean

You can delete all Aerie mission models with:

```sh
aerie-cli models clean
```

### Python API

#### Basic Usage

Instead of using the CLI for interactive use cases, you may use this package's classes to interact with Aerie as a client in your own Python scripts.

To begin, instantiate an `AerieHostSession` to connect to an Aerie host. Create an `AerieClient` instance with this session and use the methods on this class to access Aerie.

```py
from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AerieHostSession, AuthMethod

from getpass import getpass

GRAPHQL_URL = "http://myhostname:8080/v1/graphql"
GATEWAY_URL = "http://myhostname:9000"
AUTH_METHOD = AuthMethod.AERIE_NATIVE # Edit as appropriate

# Only include the following if using auth
AUTH_URL = "http://myhostname:9000/auth/login"
USERNAME = "myusername"
PASSWORD = getpass(prompt='Password: ')

session = AerieHostSession.session_helper(
    AUTH_METHOD,
    GRAPHQL_URL,
    GATEWAY_URL,
    AUTH_URL,
    USERNAME,
    PASSWORD
)

client = AerieClient(session)
plan = client.get_activity_plan_by_id(42) # Pass in ID of plan in Aerie
print(plan.name)
```

Look through the available methods in the provided `AerieClient` class to find ones that suit your needs.

#### Adding Methods

If you need to write a custom query, you can extend the `AerieClient` class and add your own method:

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
        resp = self.host_session.post_to_graphql(
            my_query,
            plan_name=plan_name
        )
        return resp[0]["id"]
```

Now, you can use your custom method like any other:

```py
# ...
client = MyCustomAerieClient(session)
plan_id = client.get_plan_id_by_name("my-plan-name")
print(plan_id)
```

#### Advanced Authentication

If you have needs for authentication (e.g., a custom token system) that aren't provided by Aerie CLI, you can use any features supported by the [Python `requests`](https://requests.readthedocs.io/en/latest/) module's [`Session` class](https://requests.readthedocs.io/en/latest/api/#request-sessions). Instantiate a session object, manipulate/add headers/cookies/SSL certificates/etc. as necessary, and use to instantiate an `AerieHostSession`:

```py
# ...
from requests import Session

my_custom_requests_session = Session()
# Manipulate as necessary
# ...

client = AerieClient(AerieHostSession(
    my_custom_requests_session,
    GRAPHQL_URL,
    GATEWAY_URL
))

# Use `AerieClient` instance as normal
```

---

## Contributing

### Contributor Installation

If you'd like to contribute to this project, you'll first need to clone this repository, and you will have to install [`poetry`](https://python-poetry.org/docs/master/).

Then, you will need to run the following commands:

1. `poetry install` -- installs the necessary dependencies into a poetry-managed virtual environment.
2. `poetry run pre-commit install` -- creates a git [pre-commit](https://pre-commit.com) hook which will automatically run formatters, style checks, etc. against your proposed commits.

### Deployment

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

Details can be found in the [twine documentation](https://twine.readthedocs.io/en/stable/index.html).

### Dependency Management

If you'd like to add or remove dependencies, you can use the `poetry add` and `poetry remove` commands, respectively. These will install the dependencies in your `poetry`-managed virtual environment, update your `pyproject.toml` file, and update your `poetry.lock` file. If you update the dependencies, you should stage and commit your changes to these two files so that others will be guaranteed to have the same Python configuration.

For more information on dependency and project management, see the [`poetry` docs](https://python-poetry.org/docs/master/).

### Testing

While developing, you'll need to use `poetry` when testing your updates. E.g.:

```
poetry run aerie-cli plans simulate --output foo.json --id 42
```

#### Unit Tests

Unit tests for both `plans` and `models` commands are contained within `tests/test_cli.py`. As of `0.11.3.1`, the unit tests are setup assuming that a local deployment of Aerie is running and ready to use. **Note: All current models and plans uploaded to Aerie will be deleted during unit test execution**.

To run unit tests, enter the following commands:

```
cd tests
poetry run pytest test_cli.py
```

The tests were developed based on `Typer` testing documentation found [here](https://typer.tiangolo.com/tutorial/testing/).

### Pre-Commit Hook

Whenever you try to commit your changes (`git commit -m "my commit message"`), you may experience errors if your current shell doesn't have access to the dependencies required for the pre-commit hook. To remedy this, simply prefix your `git` command with `poetry run`. E.g.: `poetry run git commit -m "my commit message"`.

If your code does not conform to formatting or style conventions, your commit will fail, and you will have to revise your code before committing it. Note, however, that our auto-formatter `black` does modify your files in-place when you run the pre-commit hook; you'll simply have to `git add` the changed files to stage the formatting changes, and you can attempt to commit again.

### IDE Settings

Since you are using `poetry` for development, your system Python interpreter will likely complain about any dependencies used within this project. To remedy this, you'll need to select the Python interpreter from your `poetry` virtualenv in your IDE. The method for doing so is unfortunately IDE-dependent, however.

#### VS Code

For Mac users developing in VS Code, you can achieve this by adding the following setting to your `settings.json` file:

```
"python.venvPath": "~/Library/Caches/pypoetry/virtualenvs",
```

After doing this, you can select a new Python interpreter by typing `Cmd + Shift + P` and selecting a Python interpreter which corresponds to your `poetry` virtualenv:

<img width="601" alt="image" src="https://user-images.githubusercontent.com/7908658/201275707-00caca06-5e2b-4258-b5c4-f0548134af2f.png">
