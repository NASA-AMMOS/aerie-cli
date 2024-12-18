# Integration Tests

Aerie-CLI integration tests exercise commands against an actual instance of Aerie.

## WARNING

These tests will delete and modify data permanently. Expect the localhost instance of Aerie to be modified heavily. These test will delete all models.

See: [localhost configuration](files/configuration/localhost_config.json)

## Running Locally

To set up a local test environment, use the test environment and docker-compose files in the root of the repo:

```
docker compose -f docker-compose-test.yml up
```

Invoke the tests using `pytest` from the `tests/integration_tests` directory:

```sh
python3 -m pytest .
```

## Updating Tests for New Aerie Versions

Integration tests are automatically run by CI against all supported Aerie versions. Update as follows with the supported set of Aerie versions:

1. Integration tests require a JAR for the Banananation model for each tested Aerie version. [Download official artifacts from Github](https://github.com/NASA-AMMOS/aerie/packages/1171106/versions) and add to `tests/integration_tests/files/models`, named as `banananation-X.X.X.jar` (substituting the correct version number). Remove outdated JAR files.
2. Update the `COMPATIBLE_AERIE_VERSIONS` array in [`aerie_host.py`](../../src/aerie_cli/aerie_host.py).
3. Update the [`.env`](../../.env) file `DOCKER_TAG` value to the latest compatible version. This sets the default value for a local Aerie deployment.
4. Update [`docker-compose-test.yml`](../../docker-compose-test.yml) as necessary to match the supported Aerie versions. The [aerie-ui compose file](https://github.com/NASA-AMMOS/aerie-ui/blob/develop/docker-compose-test.yml) can be a helpful reference to identify changes.
5. Update the `aerie-version` list in the [CI configuration](../../.github/workflows/test.yml) to include the new version.

To verify changes:

1. Manually run the integration tests and update the code and tests as necessary for any Aerie changes.
2. If breaking changes are necessary to support the new Aerie version, remove any Aerie versions which will no longer be supported as described above.
3. Open a PR and verify all CI tests pass.

## Summary of Integration Tests

### [Configurations test](test_configurations.py)
- Configuration initialization is in conftest.py to ensure all tests use localhost
- These tests will end with the localhost configuration active
- Test all `configurations` commands

### [Models test](test_models.py)
- Test all `models` commands

### [Plans test](test_plans.py)
- Test all `plans` commands
- Tests simulations and `plans download...` commands as well

### [Scheduling test](test_scheduling.py)
- Test all `scheduling` commands

### [Expansion test](test_expansion.py)
- Test all `expansion` commands

### [Metadata test](test_metadata.py)
- Test all `metadata` commands

### [Constraints test](test_constraints.py)
- Test all `constraints` commands
