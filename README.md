# Aerie-CLI

Aerie-CLI provides a command-line interface and user-extendable Python API for interacting with an instance of PlanDev.

> Note: this project is an informal CLI and is _not_ maintained by the MPSA PlanDev team.

## Aerie -> PlanDev Rebrand

PlanDev was **formerly known as Aerie and is now named PlanDev**. While we've updated most documentation and external references, some legacy mentions of the old product name may remain as we complete the transition.

What to know:

* The planning product, including modeling, simulation, scheduling and constraint-checking, is now named PlanDev
* The sequencing product, including the sequence editor, workspaces, and actions, is now named SeqDev
* All features and functionality remain the same
* Currently, repository names, package names and other internal code references will retain their existing names, and deployment/migration procedures have not changed
* In a future release, our repository and/or package names may change. If so, this will be communicated to users via release notes and normal communication channels

For the latest documentation, visit: [PlanDev Documentation](https://nasa-ammos.github.io/plandev-docs/)

## Getting Started

This short procedure will get you up and running with the basics of the CLI.

1. Install/update to Python >= 3.6

2. Install Aerie-CLI from Github:

   ```sh
   python3 -m pip install git+https://github.com/NASA-AMMOS/aerie-cli.git@main
   ```

3. Configure access to an PlanDev host

   1. If you've been provided a Configuration JSON, reference that file

   2. If you don't have already have a Configuration JSON, copy the following to a JSON file for a local PlanDev deployment (replacing the username with your own):

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
      aerie-cli configurations load -i JSON_FILE
      ```

4. Activate a configuration to start a session with a PlanDev host:

   ```sh
   ➜  aerie-cli activate
      1) localhost
      Select an option: 1
   ```

5. Try out a command to list the plans in PlanDev:

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

## CLI Usage

### Setup

Aerie-CLI uses configurations to define different PlanDev hosts. Define configurations by either loading JSON configurations or manually via the CLI. Configurations persist on a per-user basis and may be shared between installations.

#### Defining Hosts with a Configuration File

If you have a file of configurations to load, you can use the `configurations load` command:

```sh
aerie-cli configurations load -i JSON_FILE
```

You can view the configurations you've loaded with the `configurations list` command:

```sh
➜  aerie-cli configurations list
Configuration file location: /Users/<username>/Library/Application Support/aerie_cli/config.json

                                         PlanDev Host Configurations
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Host Name ┃ GraphQL API URL                  ┃ PlanDev Gateway URL     ┃ Username ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ localhost │ http://localhost:8080/v1/graphql │ http://localhost:9000 │          │
└───────────┴──────────────────────────────────┴───────────────────────┴──────────┘
```

#### Defining hosts via the CLI

If you haven't been provided a JSON configuration for a host, you can create a configuration by running `aerie-cli configurations create` and follow the prompts. 

#### Full Specification

Each configuration is stored as JSON object list entry in the configuration file provided with the `configurations list` command. The full contents of a host configuration are:

| Field           | Description                                                                                                                                                                         | Required |
| :-------------- |:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| -------- |
| `name`          | User-facing name of the host                                                                                                                                                        | Yes      |
| `graphql_url`   | URL of the PlanDev instance's Hasura GraphQL API                                                                                                                                    | Yes      |
| `gateway_url`   | URL of the PlanDev instance's Gateway                                                                                                                                               | Yes      |
| `username`      | Username for authentication with PlanDev                                                                                                                                            | No       |
| `external_auth` | Specification for external authentication required to reach a PlanDev instance. See [Configuring for External Authentication](#configuring-for-external-authentication) for details | No       |

### Sessions and Roles

Aerie-CLI maintains a persistent "session" with a PlanDev instance so multiple commands can run without needing to re-authenticate. To start a session, use the `activate` command:

```sh
➜  aerie-cli activate
    1) localhost
    ...
    Select an option: 1
```

PlanDev uses "roles" to adjust what a client is permitted to do. To view the active configuration name and current role, use the `status` command:

```sh
➜  aerie-cli status
Active configuration: localhost
Active role: viewer
```

The default role is configured by PlanDev. To change the selected role for the active Aerie-CLI session, use the `role` command:

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
aerie-cli --help
```

Help at command level:

```sh
aerie-cli plans --help
```

Help at sub-command level:

```sh
aerie-cli plans download --help
```

#### Interactive vs. Non-Interactive

If a command is invoked without the necessary arugments, interactive prompts are provided:

```sh
➜  aerie-cli plans download
    Id: 42
    Output: sample-output.json
```

Alternatively, arguments can be provided using flags:

```sh
➜  aerie-cli plans download --id 42 --output sample-output.json
```

#### `plans download-simulation-full-results`

Downloads simulated activities and resource timelines for a given simulation dataset, converts them into the PlanDev `SimulationResultsWriter` upload format, and writes the result to a single JSON file. This is the all-in-one equivalent of running `download-simulation` and `download-resources` separately and then converting the outputs.

**Usage:**

```sh
aerie-cli plans download-simulation-full-results --sim-id <SIMULATION_DATASET_ID> --output <OUTPUT_FILE>
```

**Arguments:**

| Flag | Short | Description |
|------|-------|-------------|
| `--sim-id` | `-s` | Simulation Dataset ID (prompted if omitted) |
| `--output` | `-o` | Output JSON file path (prompted if omitted) |

**Example:**

```sh
aerie-cli plans download-simulation-full-results --sim-id 83 --output simulation_upload.json
```

Typical output:

```
Activities       : 256 (16 with parents)
Real profiles    : 129 (130412 segments)
Discrete profiles: 45 (18130 segments)
Wrote full simulation results to simulation_upload.json
```

**Output format:**

The JSON file produced matches the `SimulationResultsWriter` format parsed by PlanDev's `uploadSimulationDataset` endpoint:

```json
{
  "simulationStartTime": "2024-002T00:00:00.000000",
  "simulationEndTime": "2024-004T00:00:00.000000",
  "profiles": {
    "realProfiles": [
      {
        "name": "BetaAngle",
        "schema": { "type": "real" },
        "segments": [
          { "extent": "00:00:30.000000", "dynamics": { "initial": 57.7, "rate": 0.0 } }
        ]
      }
    ],
    "discreteProfiles": [
      {
        "name": "SpacecraftMode",
        "schema": { "type": "string" },
        "segments": [
          { "extent": "01:19:33.200711", "dynamics": "SAFE" }
        ]
      }
    ]
  },
  "spans": {
    "simulatedActivities": [
      {
        "id": 1,
        "type": "MyActivity",
        "directiveId": 42,
        "parentId": null,
        "childIds": [],
        "startTime": "2024-002T08:00:00.000000",
        "duration": "00:30:00.000000",
        "arguments": {},
        "attributes": {}
      }
    ],
    "unfinishedActivities": []
  }
}
```

**Key format details:**

- Timestamps are DOY strings: `YYYY-DDDThh:mm:ss.ssssss`
- Durations and extents are `HH:MM:SS.ssssss` (hours not capped at 24)
- Activity `arguments` and `attributes` are raw serialized values — no `{"type","value"}` wrapper
- Real profile segment dynamics: `{"initial": <float>, "rate": <float per second>}`
- Discrete profile segment dynamics: the raw value (`"NONE"`, `false`, `[x,y,z]`, etc.)
- `childIds` are derived by inverting `parent_id` back-references across all activities
- `unfinishedActivities` is always `[]` (the CLI download has no concept of an unfinished activity)
- The simulation window is inferred: start = earliest activity `start_time`; end = start + max resource sample offset (falls back to latest activity `end_time` if there are no resources)

**Limitations:**

- `struct`-typed resources fall back to a `string` schema (not present in most models)
- All numeric resources are labeled `real`; integer-valued resources are safe as PlanDev represents them as real for profiles
- Real profile adjacent segments that share an endpoint value are merged (lossless for interpolated values, but segment count may differ from the original simulation)

### Advanced Topics

#### Configuring for External Authentication

Aerie-CLI configurations include a mechanism to authenticate against an external authentication service which may require additional credentials as cookies for accessing PlanDev. Aerie-CLI will issue a post request with given JSON data to a provided authentication endpoint and persist any returned cookies in a browser-like manner for the remainder of the Aerie-CLI session.

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

In some cases, an admin secret may be used to permit otherwise prohibited requests through Hasura (the software behind the PlanDev API). When running a command, the user may add the `--hasura-admin-secret` flag after the `aerie-cli` command to use these elevated privileges for the following command. 

---

## Python API

### Quickstart Guide

Instead of using the CLI for interactive use cases, the underlying classes and methods behind Aerie-CLI can be invoked directly in Python scripts.

The key constructs are:

- `aerie_cli.aerie_host.AerieHost`: An abstraction for a PlanDev Host, including methods for authentication and issuing requests to the PlanDev API.
- `aerie_cli.aerie_client.AerieClient`: A class containing common requests and reusable logic to interact with data in PlanDev. 

The following example defines an `AerieHost` using the necessary URLs, authenticates with a command-line prompt for the user's password, and issues a simple request using one of the built-in requests.

```py
from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AerieHost

from getpass import getpass

# These URLs define the PlanDev host
GRAPHQL_URL = "http://myhostname:8080/v1/graphql"
GATEWAY_URL = "http://myhostname:9000"

# User credentials. The password may be omitted on PlanDev instances with authentication disabled
USERNAME = "myusername"
PASSWORD = getpass(prompt='Password: ')

# Define the host and provide user credentials
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

If you need to write a custom query, you can extend the `AerieClient` class and add your own method. Access the PlanDev host using the `aerie_host` property. For example:

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

If your application will be run by a user who may also be using the CLI, you may reduce the amount of code required to configure an PlanDev host and instead just use the active session. Aerie-CLI provides a utility to retrieve an `AerieClient` instance from the active CLI session:

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

The recommended develper installation method is in a [virutual environment](https://docs.python.org/3/library/venv.html) with an [editatable install via Pip](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs). 

See this [primer](https://realpython.com/python-virtual-environments-a-primer/) or virtual environments to get set up. A quick and easy method is using Python's native `venv` package from the root of the Aerie-CLI repo:

```sh
python3 -m venv venv
source venv/bin/activate
```

Then, install Aerie-CLI in editable mode via Pip:

```sh
python3 -m pip install -e .
```

Now, your installation of Aerie-CLI will update as you make changes to the source code.

### Dependency Management

Dependencies are currently managed via Poetry. For more information on dependency and project management, see the [`poetry` docs](https://python-poetry.org/docs/master/).

### Testing

Aerie-CLI has unit tests and integration tests built with the [pytest](https://docs.pytest.org/) library.

#### Unit Tests

Unit tests can be run anytime and reference local test files. `test_aerie_client.py` is where unit tests are added to exercise particular methods of the `AerieClient` class using mocked PlanDev API responses. 

Run the unit tests using `pytest` from the `tests/unit_tests` directory:

```
cd tests
python3 -m pytest .
```

#### Integration Tests

A separate suite of tests is designed to validate CLI functionality against a local instance of PlanDev. See the [integration testing documentation](tests/integration_tests/README.md) for details.

The integration tests are based on `Typer` testing documentation found [here](https://typer.tiangolo.com/tutorial/testing/).

### Releases

Aerie-CLI generally follows the [gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) workflow model for managing releases:

- Features are merged to the `develop` branch.
- Release branches are made from develop and merge in `main` for testing.
- Releases are made from the tip of the `main` branch.
- Hotfix branches can be made from `main` to resolve bugs without needing to incorporate new features.

Version numbers are managed using [semantic versioning](https://semver.org) in [`pyproject.toml`](pyproject.toml):

- The version tag on `develop` is fixed at `0.0.0-dev0`
- Release versions are incremented on release branches before being merged to main.

The full workflow for releasing a new version of Aerie-CLI: 

- Make a release branch from `develop`
- Merge `main` into the release branch
- Commit a version increment in `pyproject.toml`
- Open a PR to merge the release branch into `main` and verify CI passes
- Merge the PR and tag a release on `main`
