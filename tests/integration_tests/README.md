# Test against an active instance of Aerie

## WARNING
These tests will delete and modify data permanently. Expect the localhost instance of Aerie to be modified heavily. These test will delete all models.

See: [localhost configuration](files/configuration/localhost_config.json)

## Tests

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