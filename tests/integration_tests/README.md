# Test against an active instance of Aerie

## WARNING
These tests will delete and modify data permanently. Expect the localhost instance of Aerie to be modified heavily. These test will delete all models.

See: [localhost configuration](files/configuration/localhost_config.json)

## Tests

### [Full test](full_test.py)
- Test all Aerie command

### [Plans test](test_plans.py)
- Test all `plans` commands
- Tests simulations and `plans download...` commands as well

### [Expansion test](test_expansion.py)
- Test all `expansion` commands