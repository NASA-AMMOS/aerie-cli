# `aerie-cli plans`

**Usage**:

```console
$ aerie-cli plans [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `clean`: Delete all activity plans.
* `create-config`: Clean and Create New Configuration for a...
* `delete`: Delete an activity plan by its id.
* `download`: Download a plan and save it locally as a...
* `download-resources`: Download resource timelines from a...
* `download-simulation`: Download simulated activity instances and...
* `duplicate`: Duplicate an existing plan.
* `list`: List uploaded plans.
* `simulate`: Simulate a plan and optionally download...
* `update-config`: Update Configuration for a Given Plan.
* `upload`: Create a plan from an input JSON file.

## `aerie-cli plans clean`

Delete all activity plans.

**Usage**:

```console
$ aerie-cli plans clean [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli plans create-config`

Clean and Create New Configuration for a Given Plan.

**Usage**:

```console
$ aerie-cli plans create-config [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: Plan ID  [required]
* `--arg-file TEXT`: JSON file with configuration arguments  [required]
* `--help`: Show this message and exit.

## `aerie-cli plans delete`

Delete an activity plan by its id.

**Usage**:

```console
$ aerie-cli plans delete [OPTIONS]
```

**Options**:

* `-p, --plan-id INTEGER`: Plan ID to be deleted  [required]
* `--help`: Show this message and exit.

## `aerie-cli plans download`

Download a plan and save it locally as a JSON file.

**Usage**:

```console
$ aerie-cli plans download [OPTIONS]
```

**Options**:

* `-p, --plan-id, --id INTEGER`: Plan ID  [required]
* `--full-args TEXT`: true, false, or comma separated list of activity types for which to get full arguments.  Otherwise only modified arguments are returned.  Defaults to false.
* `-o, --output TEXT`: The output file destination  [required]
* `--help`: Show this message and exit.

## `aerie-cli plans download-resources`

Download resource timelines from a simulation and save to either JSON or CSV.

JSON resource timelines are formatted as lists of time-value pairs. Relative timestamps are milliseconds since 
plan start time. Absolute timestamps are of the form YYYY-DDDTh:mm:ss.sss

CSV resource timeline relative timestamps are seconds since plan start time. Absolute timestamps are formatted the 
same as the JSON outputs.

**Usage**:

```console
$ aerie-cli plans download-resources [OPTIONS]
```

**Options**:

* `-s, --sim-id INTEGER`: Simulation Dataset ID  [required]
* `--csv / --json`: Specify file format. Defaults to JSON  [default: json]
* `-o, --output TEXT`: The output file destination  [required]
* `--absolute-time`: Change relative timestamps to absolute
* `--specific-states TEXT`: The file with the specific states [defaults to all]
* `--help`: Show this message and exit.

## `aerie-cli plans download-simulation`

Download simulated activity instances and save to a JSON file

**Usage**:

```console
$ aerie-cli plans download-simulation [OPTIONS]
```

**Options**:

* `-s, --sim-id INTEGER`: Simulation Dataset ID  [required]
* `-o, --output TEXT`: The output file destination  [required]
* `--help`: Show this message and exit.

## `aerie-cli plans duplicate`

Duplicate an existing plan.

**Usage**:

```console
$ aerie-cli plans duplicate [OPTIONS]
```

**Options**:

* `-p, --plan-id, --id INTEGER`: Plan ID  [required]
* `-n, --duplicate-plan-name TEXT`: The name for the duplicated plan  [required]
* `--help`: Show this message and exit.

## `aerie-cli plans list`

List uploaded plans.

**Usage**:

```console
$ aerie-cli plans list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli plans simulate`

Simulate a plan and optionally download the results.

**Usage**:

```console
$ aerie-cli plans simulate [OPTIONS]
```

**Options**:

* `--id INTEGER`: Plan ID  [required]
* `-o, --output TEXT`: The output file destination for simulation results (if desired)
* `--poll-period INTEGER`: The period (seconds) at which to poll for simulation completion  [default: 5]
* `--help`: Show this message and exit.

## `aerie-cli plans update-config`

Update Configuration for a Given Plan.

**Usage**:

```console
$ aerie-cli plans update-config [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: Plan ID  [required]
* `--arg-file TEXT`: JSON file with configuration arguments  [required]
* `--help`: Show this message and exit.

## `aerie-cli plans upload`

Create a plan from an input JSON file.

**Usage**:

```console
$ aerie-cli plans upload [OPTIONS]
```

**Options**:

* `-i, --input TEXT`: The input file from which to create an Aerie plan  [required]
* `-m, --model-id INTEGER`: The mission model ID to associate with the plan  [required]
* `--time-tag / --no-time-tag`: Append time tag to plan name  [default: no-time-tag]
* `--help`: Show this message and exit.
