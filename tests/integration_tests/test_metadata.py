import os

from aerie_cli.__main__ import app

from .conftest import RUNNER

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

METADATA_SCHEMAS_PATH = os.path.join(FILES_PATH, "metadata_schemas")
METADATA_SCHEMA_PATH = os.path.join(METADATA_SCHEMAS_PATH, "metadata_schema.json")

def test_metadata_list():
    result = RUNNER.invoke(app, ["metadata", "list"],
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Metadata Schemas" in result.stdout

def test_metadata_clean():
    result = RUNNER.invoke(app, ["metadata", "clean"],
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "All metadata schemas have been deleted" in result.stdout

def test_metadata_upload():
    result = RUNNER.invoke(app, ["metadata", "upload"],
                           input=METADATA_SCHEMA_PATH,
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "2 new schema have been added" in result.stdout

def test_metadata_delete():
    result = RUNNER.invoke(app, ["metadata", "delete"],
                           input="STRING_EXAMPLE",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Schema `STRING_EXAMPLE` has been removed" in result.stdout
