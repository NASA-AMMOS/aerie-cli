# `aerie-cli metadata`

**Usage**:

```console
$ aerie-cli metadata [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `clean`: Delete all metadata schemas.
* `delete`: Delete a metadata schema by its name.
* `list`: List uploaded metadata schemas.
* `upload`: Add to the metadata schema from a .json file.

## `aerie-cli metadata clean`

Delete all metadata schemas.

**Usage**:

```console
$ aerie-cli metadata clean [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli metadata delete`

Delete a metadata schema by its name.

**Usage**:

```console
$ aerie-cli metadata delete [OPTIONS]
```

**Options**:

* `-n, --schema-name TEXT`: Name of schema to be deleted  [required]
* `--help`: Show this message and exit.

## `aerie-cli metadata list`

List uploaded metadata schemas.

**Usage**:

```console
$ aerie-cli metadata list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli metadata upload`

Add to the metadata schema from a .json file.

JSON file contents should include a list schemas, each containing a key for its name and value for its type.

**Usage**:

```console
$ aerie-cli metadata upload [OPTIONS]
```

**Options**:

* `-i, --schema-path TEXT`: path to JSON file defining the schema to be created  [required]
* `--help`: Show this message and exit.
