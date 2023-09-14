# `aerie-cli models`

**Usage**:

```console
$ aerie-cli models [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `clean`: Delete all mission models.
* `delete`: Delete a mission model by its model id.
* `list`: List uploaded mission models.
* `upload`: Upload a single mission model from a .jar...

## `aerie-cli models clean`

Delete all mission models.

**Usage**:

```console
$ aerie-cli models clean [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli models delete`

Delete a mission model by its model id.

**Usage**:

```console
$ aerie-cli models delete [OPTIONS]
```

**Options**:

* `-m, --model-id INTEGER`: Mission model ID to be deleted  [required]
* `--help`: Show this message and exit.

## `aerie-cli models list`

List uploaded mission models.

**Usage**:

```console
$ aerie-cli models list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli models upload`

Upload a single mission model from a .jar file.

**Usage**:

```console
$ aerie-cli models upload [OPTIONS]
```

**Options**:

* `-i, --mission-model-path TEXT`: The input file from which to create an Aerie model  [required]
* `-n, --model-name TEXT`: Name of mission model  [required]
* `-v, --version TEXT`: Mission model verison
* `--time-tag-version`: Use timestamp for model version
* `--sim-template TEXT`: Simulation template file
* `--help`: Show this message and exit.
