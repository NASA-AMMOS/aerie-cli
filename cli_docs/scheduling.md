# `aerie-cli scheduling`

**Usage**:

```console
$ aerie-cli scheduling [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `delete`: Delete scheduling goal
* `delete-all-goals-for-plan`
* `upload`: Upload scheduling goal

## `aerie-cli scheduling delete`

Delete scheduling goal

**Usage**:

```console
$ aerie-cli scheduling delete [OPTIONS]
```

**Options**:

* `--goal-id INTEGER`: Goal ID of goal to be deleted  [required]
* `--help`: Show this message and exit.

## `aerie-cli scheduling delete-all-goals-for-plan`

**Usage**:

```console
$ aerie-cli scheduling delete-all-goals-for-plan [OPTIONS]
```

**Options**:

* `--plan-id INTEGER`: Plan ID  [required]
* `--help`: Show this message and exit.

## `aerie-cli scheduling upload`

Upload scheduling goal

**Usage**:

```console
$ aerie-cli scheduling upload [OPTIONS]
```

**Options**:

* `--model-id INTEGER`: The mission model ID to associate with the scheduling goal  [required]
* `--plan-id INTEGER`: Plan ID  [required]
* `--schedule TEXT`: Text file with one path on each line to a scheduling rule file, in decreasing priority order  [required]
* `--help`: Show this message and exit.
