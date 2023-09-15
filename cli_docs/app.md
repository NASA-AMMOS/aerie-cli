# `aerie-cli app`

**Usage**:

```console
$ aerie-cli app [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-v, --version`: Print Aerie-CLI package version and exit.
* `--hasura-admin-secret TEXT`: Hasura admin secret that will be put in the header of graphql requests.
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `activate`: Activate a session with an Aerie host...
* `configurations`
* `constraints`
* `deactivate`: Deactivate any active session
* `expansion`
* `metadata`
* `models`
* `plans`
* `role`: Change Aerie permissions role for the...
* `scheduling`
* `status`: Returns information about the current...

## `aerie-cli app activate`

Activate a session with an Aerie host using a given configuration

**Usage**:

```console
$ aerie-cli app activate [OPTIONS]
```

**Options**:

* `-n, --name NAME`: Name for this configuration
* `-r, --role ROLE`: Specify a non-default role
* `--help`: Show this message and exit.

## `aerie-cli app configurations`

**Usage**:

```console
$ aerie-cli app configurations [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `activate`: Activate a session with an Aerie host...
* `clean`: Remove all persistent aerie-cli files
* `create`: Define a configuration for an Aerie host
* `deactivate`: Deactivate any active session
* `delete`: Delete an Aerie host configuration
* `list`: List available Aerie host configurations
* `load`: Load one or more configurations from a...
* `update`: Update an existing configuration for an...

### `aerie-cli app configurations activate`

Activate a session with an Aerie host using a given configuration

**Usage**:

```console
$ aerie-cli app configurations activate [OPTIONS]
```

**Options**:

* `-n, --name NAME`: Name for this configuration
* `--help`: Show this message and exit.

### `aerie-cli app configurations clean`

Remove all persistent aerie-cli files

**Usage**:

```console
$ aerie-cli app configurations clean [OPTIONS]
```

**Options**:

* `--not-interactive / --no-not-interactive`: Disable interactive prompt  [default: no-not-interactive]
* `--help`: Show this message and exit.

### `aerie-cli app configurations create`

Define a configuration for an Aerie host

**Usage**:

```console
$ aerie-cli app configurations create [OPTIONS]
```

**Options**:

* `--name NAME`: Name for this configuration  [required]
* `--graphql-url GRAPHQL_URL`: URL of GraphQL API endpoint  [required]
* `--gateway-url GATEWAY_URL`: URL of Aerie Gateway  [required]
* `--auth-method [None|Native|Cookie]`: Authentication method  [default: None]
* `--auth-url AUTH_URL`: URL of Authentication endpoint
* `--username USERNAME`: Username for authentication
* `--help`: Show this message and exit.

### `aerie-cli app configurations deactivate`

Deactivate any active session

**Usage**:

```console
$ aerie-cli app configurations deactivate [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app configurations delete`

Delete an Aerie host configuration

**Usage**:

```console
$ aerie-cli app configurations delete [OPTIONS]
```

**Options**:

* `-n, --name NAME`: Name for this configuration
* `--help`: Show this message and exit.

### `aerie-cli app configurations list`

List available Aerie host configurations

**Usage**:

```console
$ aerie-cli app configurations list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app configurations load`

Load one or more configurations from a JSON file

**Usage**:

```console
$ aerie-cli app configurations load [OPTIONS]
```

**Options**:

* `-i, --filename PATH`: Name of input JSON file  [required]
* `--allow-overwrite`: Allow overwriting existing configurations
* `--help`: Show this message and exit.

### `aerie-cli app configurations update`

Update an existing configuration for an Aerie host

**Usage**:

```console
$ aerie-cli app configurations update [OPTIONS]
```

**Options**:

* `-n, --name NAME`: Name of the configuration to update
* `--help`: Show this message and exit.

## `aerie-cli app constraints`

**Usage**:

```console
$ aerie-cli app constraints [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `delete`: Delete a constraint
* `update`: Update a constraint
* `upload`: Upload a constraint
* `violations`

### `aerie-cli app constraints delete`

Delete a constraint

**Usage**:

```console
$ aerie-cli app constraints delete [OPTIONS]
```

**Options**:

* `--id INTEGER`: The constraint id to be deleted  [required]
* `--help`: Show this message and exit.

### `aerie-cli app constraints update`

Update a constraint

**Usage**:

```console
$ aerie-cli app constraints update [OPTIONS]
```

**Options**:

* `--id INTEGER`: The constraint id to be modifyed  [required]
* `--constraint-file TEXT`: The new constraint for the id  [required]
* `--help`: Show this message and exit.

### `aerie-cli app constraints upload`

Upload a constraint

**Usage**:

```console
$ aerie-cli app constraints upload [OPTIONS]
```

**Options**:

* `--model-id INTEGER`: The model id associated with the constraint (do not input plan id)
* `--plan-id INTEGER`: The plan id associated with the constraint (do not input model id)
* `--name TEXT`: The name of the constraint  [required]
* `--summary TEXT`: The summary of the constraint
* `--description TEXT`: The description of the constraint
* `--constraint-file TEXT`: The file that holds the constraint  [required]
* `--help`: Show this message and exit.

### `aerie-cli app constraints violations`

**Usage**:

```console
$ aerie-cli app constraints violations [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: The plan id for the violation  [required]
* `--help`: Show this message and exit.

## `aerie-cli app deactivate`

Deactivate any active session

**Usage**:

```console
$ aerie-cli app deactivate [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli app expansion`

**Usage**:

```console
$ aerie-cli app expansion [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `runs`: Commands for expansion runs
* `sequences`: Commands for sequences
* `sets`: Commands for expansion sets

### `aerie-cli app expansion runs`

Commands for expansion runs

**Usage**:

```console
$ aerie-cli app expansion runs [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Run command expansion on a simulation dataset
* `list`: List expansion runs for a given plan or...

#### `aerie-cli app expansion runs create`

Run command expansion on a simulation dataset

**Usage**:

```console
$ aerie-cli app expansion runs create [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-e, --expansion-set TEXT`: Expansion Set ID  [required]
* `--help`: Show this message and exit.

#### `aerie-cli app expansion runs list`

List expansion runs for a given plan or simulation dataset

Runs are listed in reverse chronological order.

**Usage**:

```console
$ aerie-cli app expansion runs list [OPTIONS]
```

**Options**:

* `-p, --plan-id TEXT`: Plan ID
* `-s, --sim-id TEXT`: Simulation Dataset ID
* `--help`: Show this message and exit.

### `aerie-cli app expansion sequences`

Commands for sequences

**Usage**:

```console
$ aerie-cli app expansion sequences [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a sequence on a simulation dataset
* `delete`: Delete sequence on a simulation dataset
* `download`: Download a SeqJson file from an Aerie...
* `list`: List sequences for a given plan or...

#### `aerie-cli app expansion sequences create`

Create a sequence on a simulation dataset

**Usage**:

```console
$ aerie-cli app expansion sequences create [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-t, --sequence-id TEXT`: Sequence ID to download  [required]
* `--help`: Show this message and exit.

#### `aerie-cli app expansion sequences delete`

Delete sequence on a simulation dataset

**Usage**:

```console
$ aerie-cli app expansion sequences delete [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-t, --sequence-id TEXT`: Sequence ID to download  [required]
* `--help`: Show this message and exit.

#### `aerie-cli app expansion sequences download`

Download a SeqJson file from an Aerie sequence

**Usage**:

```console
$ aerie-cli app expansion sequences download [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-t, --sequence-id TEXT`: Sequence ID to download  [required]
* `-o, --output TEXT`: Name of output JSON file  [required]
* `--help`: Show this message and exit.

#### `aerie-cli app expansion sequences list`

List sequences for a given plan or simulation dataset

Sequences are listed in alphabetical order.

**Usage**:

```console
$ aerie-cli app expansion sequences list [OPTIONS]
```

**Options**:

* `-p, --plan-id TEXT`: Plan ID
* `-s, --sim-id TEXT`: Simulation Dataset ID
* `--help`: Show this message and exit.

### `aerie-cli app expansion sets`

Commands for expansion sets

**Usage**:

```console
$ aerie-cli app expansion sets [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create an expansion set
* `get`: View all rules in an expansion set
* `list`: List all expansion sets

#### `aerie-cli app expansion sets create`

Create an expansion set

Uses the newest expansion rules for each given activity type.
Filters to only use rules designated for the given mission model and 
command dictionary.

**Usage**:

```console
$ aerie-cli app expansion sets create [OPTIONS]
```

**Options**:

* `-m, --model-id INTEGER`: Mission Model ID  [required]
* `-d, --command-dict-id INTEGER`: Command Dictionary ID  [required]
* `-a, --activity-types TEXT`: Activity types to be included in the set
* `--help`: Show this message and exit.

#### `aerie-cli app expansion sets get`

View all rules in an expansion set

**Usage**:

```console
$ aerie-cli app expansion sets get [OPTIONS]
```

**Options**:

* `-e, --expansion-set TEXT`: Expansion Set ID  [required]
* `--help`: Show this message and exit.

#### `aerie-cli app expansion sets list`

List all expansion sets

**Usage**:

```console
$ aerie-cli app expansion sets list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli app metadata`

**Usage**:

```console
$ aerie-cli app metadata [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `clean`: Delete all metadata schemas.
* `delete`: Delete a metadata schema by its name.
* `list`: List uploaded metadata schemas.
* `upload`: Add to the metadata schema from a .json file.

### `aerie-cli app metadata clean`

Delete all metadata schemas.

**Usage**:

```console
$ aerie-cli app metadata clean [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app metadata delete`

Delete a metadata schema by its name.

**Usage**:

```console
$ aerie-cli app metadata delete [OPTIONS]
```

**Options**:

* `-n, --schema-name TEXT`: Name of schema to be deleted  [required]
* `--help`: Show this message and exit.

### `aerie-cli app metadata list`

List uploaded metadata schemas.

**Usage**:

```console
$ aerie-cli app metadata list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app metadata upload`

Add to the metadata schema from a .json file.

JSON file contents should include a list schemas, each containing a key for its name and value for its type.

**Usage**:

```console
$ aerie-cli app metadata upload [OPTIONS]
```

**Options**:

* `-i, --schema-path TEXT`: path to JSON file defining the schema to be created  [required]
* `--help`: Show this message and exit.

## `aerie-cli app models`

**Usage**:

```console
$ aerie-cli app models [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `clean`: Delete all mission models.
* `delete`: Delete a mission model by its model id.
* `list`: List uploaded mission models.
* `upload`: Upload a single mission model from a .jar...

### `aerie-cli app models clean`

Delete all mission models.

**Usage**:

```console
$ aerie-cli app models clean [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app models delete`

Delete a mission model by its model id.

**Usage**:

```console
$ aerie-cli app models delete [OPTIONS]
```

**Options**:

* `-m, --model-id INTEGER`: Mission model ID to be deleted  [required]
* `--help`: Show this message and exit.

### `aerie-cli app models list`

List uploaded mission models.

**Usage**:

```console
$ aerie-cli app models list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app models upload`

Upload a single mission model from a .jar file.

**Usage**:

```console
$ aerie-cli app models upload [OPTIONS]
```

**Options**:

* `-i, --mission-model-path TEXT`: The input file from which to create an Aerie model  [required]
* `-n, --model-name TEXT`: Name of mission model  [required]
* `-v, --version TEXT`: Mission model verison
* `--time-tag-version`: Use timestamp for model version
* `--sim-template TEXT`: Simulation template file
* `--help`: Show this message and exit.

## `aerie-cli app plans`

**Usage**:

```console
$ aerie-cli app plans [OPTIONS] COMMAND [ARGS]...
```

**Options**:

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

### `aerie-cli app plans clean`

Delete all activity plans.

**Usage**:

```console
$ aerie-cli app plans clean [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app plans create-config`

Clean and Create New Configuration for a Given Plan.

**Usage**:

```console
$ aerie-cli app plans create-config [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: Plan ID  [required]
* `--arg-file TEXT`: JSON file with configuration arguments  [required]
* `--help`: Show this message and exit.

### `aerie-cli app plans delete`

Delete an activity plan by its id.

**Usage**:

```console
$ aerie-cli app plans delete [OPTIONS]
```

**Options**:

* `-p, --plan-id INTEGER`: Plan ID to be deleted  [required]
* `--help`: Show this message and exit.

### `aerie-cli app plans download`

Download a plan and save it locally as a JSON file.

**Usage**:

```console
$ aerie-cli app plans download [OPTIONS]
```

**Options**:

* `-p, --plan-id, --id INTEGER`: Plan ID  [required]
* `--full-args TEXT`: true, false, or comma separated list of activity types for which to get full arguments.  Otherwise only modified arguments are returned.  Defaults to false.
* `-o, --output TEXT`: The output file destination  [required]
* `--help`: Show this message and exit.

### `aerie-cli app plans download-resources`

Download resource timelines from a simulation and save to either JSON or CSV.

JSON resource timelines are formatted as lists of time-value pairs. Relative timestamps are milliseconds since 
plan start time. Absolute timestamps are of the form YYYY-DDDTh:mm:ss.sss

CSV resource timeline relative timestamps are seconds since plan start time. Absolute timestamps are formatted the 
same as the JSON outputs.

**Usage**:

```console
$ aerie-cli app plans download-resources [OPTIONS]
```

**Options**:

* `-s, --sim-id INTEGER`: Simulation Dataset ID  [required]
* `--csv / --json`: Specify file format. Defaults to JSON  [default: json]
* `-o, --output TEXT`: The output file destination  [required]
* `--absolute-time`: Change relative timestamps to absolute
* `--specific-states TEXT`: The file with the specific states [defaults to all]
* `--help`: Show this message and exit.

### `aerie-cli app plans download-simulation`

Download simulated activity instances and save to a JSON file

**Usage**:

```console
$ aerie-cli app plans download-simulation [OPTIONS]
```

**Options**:

* `-s, --sim-id INTEGER`: Simulation Dataset ID  [required]
* `-o, --output TEXT`: The output file destination  [required]
* `--help`: Show this message and exit.

### `aerie-cli app plans duplicate`

Duplicate an existing plan.

**Usage**:

```console
$ aerie-cli app plans duplicate [OPTIONS]
```

**Options**:

* `-p, --plan-id, --id INTEGER`: Plan ID  [required]
* `-n, --duplicate-plan-name TEXT`: The name for the duplicated plan  [required]
* `--help`: Show this message and exit.

### `aerie-cli app plans list`

List uploaded plans.

**Usage**:

```console
$ aerie-cli app plans list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `aerie-cli app plans simulate`

Simulate a plan and optionally download the results.

**Usage**:

```console
$ aerie-cli app plans simulate [OPTIONS]
```

**Options**:

* `--id INTEGER`: Plan ID  [required]
* `-o, --output TEXT`: The output file destination for simulation results (if desired)
* `--poll-period INTEGER`: The period (seconds) at which to poll for simulation completion  [default: 5]
* `--help`: Show this message and exit.

### `aerie-cli app plans update-config`

Update Configuration for a Given Plan.

**Usage**:

```console
$ aerie-cli app plans update-config [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: Plan ID  [required]
* `--arg-file TEXT`: JSON file with configuration arguments  [required]
* `--help`: Show this message and exit.

### `aerie-cli app plans upload`

Create a plan from an input JSON file.

**Usage**:

```console
$ aerie-cli app plans upload [OPTIONS]
```

**Options**:

* `-i, --input TEXT`: The input file from which to create an Aerie plan  [required]
* `-m, --model-id INTEGER`: The mission model ID to associate with the plan  [required]
* `--time-tag / --no-time-tag`: Append time tag to plan name  [default: no-time-tag]
* `--help`: Show this message and exit.

## `aerie-cli app role`

Change Aerie permissions role for the active session

**Usage**:

```console
$ aerie-cli app role [OPTIONS]
```

**Options**:

* `-r, --role ROLE`: New role to selec
* `--help`: Show this message and exit.

## `aerie-cli app scheduling`

**Usage**:

```console
$ aerie-cli app scheduling [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `delete`: Delete scheduling goal
* `delete-all-goals-for-plan`
* `upload`: Upload scheduling goal to single plan or...

### `aerie-cli app scheduling delete`

Delete scheduling goal

**Usage**:

```console
$ aerie-cli app scheduling delete [OPTIONS]
```

**Options**:

* `--goal-id INTEGER`: Goal ID of goal to be deleted  [required]
* `--help`: Show this message and exit.

### `aerie-cli app scheduling delete-all-goals-for-plan`

**Usage**:

```console
$ aerie-cli app scheduling delete-all-goals-for-plan [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: Plan ID  [required]
* `--help`: Show this message and exit.

### `aerie-cli app scheduling upload`

Upload scheduling goal to single plan or to all plans in a model

**Usage**:

```console
$ aerie-cli app scheduling upload [OPTIONS]
```

**Options**:

* `-m, --model-id INTEGER`: The mission model ID to associate with the scheduling goal
* `-p, --plan-id INTEGER`: Plan ID
* `-f, --file-path TEXT`: Text file with one path on each line to a scheduling rule file, in decreasing priority order
* `--help`: Show this message and exit.

## `aerie-cli app status`

Returns information about the current Aerie session.

**Usage**:

```console
$ aerie-cli app status [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
