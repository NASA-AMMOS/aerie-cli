# Aerie CLI

Note: this project is an informal CLI and is _not_ maintained by the MPSA Aerie team.

##### Table of Contents

- [Overview](#overview)
- [Installation](#installation)
  - [Installation with `pip`](#installation-with-pip)
  - [Installation with `poetry`](#installation-with-poetry)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [`AerieClient` Usage](#ide-configuration)
- [Contributing](#contributing)

---

## Overview

TBD...

---

## Installation

### Installation with `pip`

Assuming you have Python installed on your system, you can install `aerie-cli` with the following command:

```sh
python -m pip install git+https://github.jpl.nasa.gov/397/aerie-cli.git#main
```

Note: if `python` points to a system-provided Python 2 installation, you should instead use `python3`.

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
If you want to install from a specific branch of `aerie-cli` replace `#main` in the GitHub url with `@branchname` as following:

```sh
$ python3 -m pip install git+https://github.jpl.nasa.gov/397/aerie-cli.git@branchname
```

### Installation with `poetry`

If you use `poetry` for your dependency management and intend to use this package in another Python project, you can install this package to an existing `poetry` project with:

```sh
poetry add git+https://github.jpl.nasa.gov/397/aerie-cli.git#main
```

For more info on `poetry`, see the [Contributing](#contributing) section below.

---

## Usage

### CLI Usage

We're using the [`typer`](https://typer.tiangolo.com) library for command-line input. This allows us to run any of these commands interactively (with user prompts for each un-provided argument) OR non-interactively (where all are provided).

**Note**: during the early stages of development, the examples in this README may not be perfectly in sync with updates to the commands and sub-commands supported by the CLI. If there is any discrepancy, you're encouraged to use the `--help` option (see [Help](#help) section) for information on commands and sub-commands in your specific CLI version.

#### Interactive

For example, we can run a script without any CLI args/options, and we'll be prompted for the necessary information:

```sh
>>> aerie-cli plans download
> Username: myusername
> Password: <hidden>
> Id: 42
> Output: sample-output.json
```

#### Non-Interactive

Alternatively, if we get tired of repeatedly providing the same inputs (or want to build automation on top of our CLI), we can provide the arguments directly as we invoke the CLI:

```sh
>>> aerie-cli plans download --username myusername --id 42 --output sample-output.json
> Password: <hidden>
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
  --username TEXT    JPL username  [required]
  --password TEXT    JPL password  [required]
  --id INTEGER       Plan ID  [required]
  --output TEXT      The output file destination  [required]
  --server-url TEXT  The URL of the Aerie deployment  [default:
                     http://localhost]
  --help             Show this message and exit.
```

#### Specific Sub-Commands

##### Plan Download

You can download an Aerie plan simply as such:

```sh
aerie-cli plans download
```

The output JSON file resembles the plan as hosted on the Aerie deployment.

##### Plan Upload

You can upload an Aerie plan simply with:

```sh
aerie-cli plans upload
```

NOTE: a downloaded JSON plan includes arguments for `id` (plan ID), `model_id` (mission model / adaptation ID), and an `id` for each activity instance. These are included for the convenience of the user, but if the same downloaded plan is used for upload, these fields are ignored (since new activity instances and a new plan container are created for an upload). You may feel free to delete these fields from persisted plans if you'd like.

##### Plan Duplication

You can duplicate an Aerie plan (create a copy against the same mission model) with:

```sh
aerie-cli plans duplicate
```

##### Plan Simulation

You can simulate an Aerie plan with:

```sh
aerie-cli plans simulate
```

If an `--output` argument isn't provided, this will simply run a simulation so that the results are cached on the server and are quickly visible in the UI. However, if you want to persist the results in JSON form, you should provide an `--output` path to a local file.

### `AerieClient` Usage

Instead of using the CLI for interactive use cases, you may use this package's classes to interact with Aerie as a client in your own Python scripts.

For example, consider the simple Python script:

```py
from aerie_cli.client import Auth, AerieClient

USERNAME = "myusername"
# NOTE: you are not recommended to store your password in plaintext in the source file
PASSWORD = "mysupersecretpassword"
PLAN_ID = 42 # should match a plan ID hosted on Aerie

auth = Auth(USERNAME, PASSWORD)
client = AerieClient(server_url="http://localhost", auth=auth)

plan = client.get_activity_plan(PLAN_ID)

print(plan.name)
```

This example shows that we can create an `AerieClient` object given an Aerie deployment URL and JPL credentials. The `AerieClient` class exposes several useful methods like `get_activity_plan()`, `create_activity_plan()`, `simulate_plan()`, and more. While this package is in early development, consult the source code and docstrings for the latest and greatest client methods.

---

## Contributing

TBD...
