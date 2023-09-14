# `aerie-cli expansion`

**Usage**:

```console
$ aerie-cli expansion [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `runs`: Commands for expansion runs
* `sequences`: Commands for sequences
* `sets`: Commands for expansion sets

## `aerie-cli expansion runs`

Commands for expansion runs

**Usage**:

```console
$ aerie-cli expansion runs [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Run command expansion on a simulation dataset
* `list`: List expansion runs for a given plan or...

### `aerie-cli expansion runs create`

Run command expansion on a simulation dataset

**Usage**:

```console
$ aerie-cli expansion runs create [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-e, --expansion-set TEXT`: Expansion Set ID  [required]
* `--help`: Show this message and exit.

### `aerie-cli expansion runs list`

List expansion runs for a given plan or simulation dataset

Runs are listed in reverse chronological order.

**Usage**:

```console
$ aerie-cli expansion runs list [OPTIONS]
```

**Options**:

* `-p, --plan-id TEXT`: Plan ID
* `-s, --sim-id TEXT`: Simulation Dataset ID
* `--help`: Show this message and exit.

## `aerie-cli expansion sequences`

Commands for sequences

**Usage**:

```console
$ aerie-cli expansion sequences [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a sequence on a simulation dataset
* `delete`: Delete sequence on a simulation dataset
* `download`: Download a SeqJson file from an Aerie...
* `list`: List sequences for a given plan or...

### `aerie-cli expansion sequences create`

Create a sequence on a simulation dataset

**Usage**:

```console
$ aerie-cli expansion sequences create [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-t, --sequence-id TEXT`: Sequence ID to download  [required]
* `--help`: Show this message and exit.

### `aerie-cli expansion sequences delete`

Delete sequence on a simulation dataset

**Usage**:

```console
$ aerie-cli expansion sequences delete [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-t, --sequence-id TEXT`: Sequence ID to download  [required]
* `--help`: Show this message and exit.

### `aerie-cli expansion sequences download`

Download a SeqJson file from an Aerie sequence

**Usage**:

```console
$ aerie-cli expansion sequences download [OPTIONS]
```

**Options**:

* `-s, --sim-id TEXT`: Simulation Dataset ID  [required]
* `-t, --sequence-id TEXT`: Sequence ID to download  [required]
* `-o, --output TEXT`: Name of output JSON file  [required]
* `--help`: Show this message and exit.

### `aerie-cli expansion sequences list`

List sequences for a given plan or simulation dataset

Sequences are listed in alphabetical order.

**Usage**:

```console
$ aerie-cli expansion sequences list [OPTIONS]
```

**Options**:

* `-p, --plan-id TEXT`: Plan ID
* `-s, --sim-id TEXT`: Simulation Dataset ID
* `--help`: Show this message and exit.

## `aerie-cli expansion sets`

Commands for expansion sets

**Usage**:

```console
$ aerie-cli expansion sets [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create an expansion set
* `get`: View all rules in an expansion set
* `list`: List all expansion sets

### `aerie-cli expansion sets create`

Create an expansion set

Uses the newest expansion rules for each given activity type.
Filters to only use rules designated for the given mission model and 
command dictionary.

**Usage**:

```console
$ aerie-cli expansion sets create [OPTIONS]
```

**Options**:

* `-m, --model-id INTEGER`: Mission Model ID  [required]
* `-d, --command-dict-id INTEGER`: Command Dictionary ID  [required]
* `-a, --activity-types TEXT`: Activity types to be included in the set
* `--help`: Show this message and exit.

### `aerie-cli expansion sets get`

View all rules in an expansion set

**Usage**:

```console
$ aerie-cli expansion sets get [OPTIONS]
```

**Options**:

* `-e, --expansion-set TEXT`: Expansion Set ID  [required]
* `--help`: Show this message and exit.

### `aerie-cli expansion sets list`

List all expansion sets

**Usage**:

```console
$ aerie-cli expansion sets list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
