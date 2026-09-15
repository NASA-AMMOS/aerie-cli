# Integration Tests

PlanDev-CLI integration tests exercise commands against an actual instance of PlanDev.

## WARNING

These tests will delete and modify data permanently. Expect the localhost instance of PlanDev to be modified heavily. These test will delete all models.

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

## Updating Tests for New PlanDev Versions

Integration tests are automatically run by CI against all supported PlanDev versions. Update as follows with the supported set of PlanDev versions:

1. Integration tests require a JAR for the Banananation model for each tested PlanDev version. [Download official artifacts from Github](https://github.com/NASA-AMMOS/plandev/packages/1171106/versions) and add to `tests/integration_tests/files/models`, named as `banananation-X.X.X.jar` (substituting the correct version number). Remove outdated JAR files.
2. Update the `COMPATIBLE_PLANDEV_VERSIONS` array in [`plandev_host.py`](../../src/plandev_cli/plandev_host.py).
3. Update the [`.env`](../../.env) file `DOCKER_TAG` value to the latest compatible version. This sets the default value for a local PlanDev deployment.
4. Update [`docker-compose-test.yml`](../../docker-compose-test.yml) as necessary to match the supported PlanDev versions. The [plandev-ui compose file](https://github.com/NASA-AMMOS/plandev-ui/blob/develop/docker-compose-test.yml) can be a helpful reference to identify changes.

To verify changes:

1. Manually run the integration tests and update the code and tests as necessary for any PlanDev changes.
2. If breaking changes are necessary to support the new PlanDev version, remove any PlanDev versions which will no longer be supported as described above.
3. Open a PR and verify all CI tests pass.
