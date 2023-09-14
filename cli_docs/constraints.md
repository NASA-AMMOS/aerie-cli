# `aerie-cli constraints`

**Usage**:

```console
$ aerie-cli constraints [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `delete`: Delete a constraint
* `update`: Update a constraint
* `upload`: Upload a constraint
* `violations`

## `aerie-cli constraints delete`

Delete a constraint

**Usage**:

```console
$ aerie-cli constraints delete [OPTIONS]
```

**Options**:

* `--id INTEGER`: The constraint id to be deleted  [required]
* `--help`: Show this message and exit.

## `aerie-cli constraints update`

Update a constraint

**Usage**:

```console
$ aerie-cli constraints update [OPTIONS]
```

**Options**:

* `--id INTEGER`: The constraint id to be modifyed  [required]
* `--constraint-file TEXT`: The new constraint for the id  [required]
* `--help`: Show this message and exit.

## `aerie-cli constraints upload`

Upload a constraint

**Usage**:

```console
$ aerie-cli constraints upload [OPTIONS]
```

**Options**:

* `--model-id INTEGER`: The model id associated with the constraint (do not input plan id)
* `--plan-id INTEGER`: The plan id associated with the constraint (do not input model id)
* `--name TEXT`: The name of the constraint  [required]
* `--description TEXT`: The description of the constraint
* `--constraint-file TEXT`: The file that holds the constraint  [required]
* `--help`: Show this message and exit.

## `aerie-cli constraints violations`

**Usage**:

```console
$ aerie-cli constraints violations [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: The plan id for the violation  [required]
* `--help`: Show this message and exit.
