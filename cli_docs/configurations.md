# `aerie-cli configurations`

**Usage**:

```console
$ aerie-cli configurations [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `clean`: Remove all persistent aerie-cli files
* `create`: Define a configuration for an Aerie host
* `delete`: Delete an Aerie host configuration
* `list`: List available Aerie host configurations
* `load`: Load one or more configurations from a...

## `aerie-cli configurations clean`

Remove all persistent aerie-cli files

**Usage**:

```console
$ aerie-cli configurations clean [OPTIONS]
```

**Options**:

* `--not-interactive / --no-not-interactive`: Disable interactive prompt  [default: no-not-interactive]
* `--help`: Show this message and exit.

## `aerie-cli configurations create`

Define a configuration for an Aerie host

**Usage**:

```console
$ aerie-cli configurations create [OPTIONS]
```

**Options**:

* `--name NAME`: Name for this configuration  [required]
* `--graphql-url GRAPHQL_URL`: URL of GraphQL API endpoint  [required]
* `--gateway-url GATEWAY_URL`: URL of Aerie Gateway  [required]
* `--username USERNAME`: Username for authentication
* `--help`: Show this message and exit.

## `aerie-cli configurations delete`

Delete an Aerie host configuration

**Usage**:

```console
$ aerie-cli configurations delete [OPTIONS]
```

**Options**:

* `-n, --name NAME`: Name for this configuration
* `--help`: Show this message and exit.

## `aerie-cli configurations list`

List available Aerie host configurations

**Usage**:

```console
$ aerie-cli configurations list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `aerie-cli configurations load`

Load one or more configurations from a JSON file

**Usage**:

```console
$ aerie-cli configurations load [OPTIONS]
```

**Options**:

* `-i, --filename PATH`: Name of input JSON file  [required]
* `--allow-overwrite`: Allow overwriting existing configurations
* `--help`: Show this message and exit.
