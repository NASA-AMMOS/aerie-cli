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

Integration tests are automatically run by CI against all supported Aerie versions. To add and test support for a new Aerie version:

1. Download the appropriate version release JAR for the [Banananation model](https://github.com/NASA-AMMOS/aerie/packages/1171106/versions) and add it to `tests/integration_tests/models`, named as `banananation-X.X.X.jar` (substituting the correct version number).
2. Update the [`.env`](../../.env) file `DOCKER_TAG` value to the new version string. This defaults the local deployment to the latest Aerie version.
3. Update [`docker-compose-test.yml`](../../docker-compose-test.yml) as necessary to match the new Aerie version. The [aerie-ui compose file](https://github.com/NASA-AMMOS/aerie-ui/blob/develop/docker-compose-test.yml) can be a helpful reference to identify changes.
4. Manually run the integration tests and update the code and tests as necessary for any Aerie changes.
5. Update the `aerie-version` list in the [CI configuration](../../.github/workflows/test.yml) to include the new version.
6. If breaking changes are necessary to support the new Aerie version, remove any Aerie versions which are no longer supported from the CI configuration and remove the corresponding banananation JAR file.
7. Open a PR and verify all tests still pass.

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
