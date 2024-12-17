import json
from pathlib import Path
from typing import List

from aerie_cli.schemas.client import DictionaryType
from aerie_cli.schemas.client import DictionaryMetadata
from aerie_cli.schemas.client import Parcel

from .conftest import client

ARTIFACTS_PATH = Path(__file__).parent.joinpath("artifacts", "parcels")
DICTIONARIES_PATH = Path(__file__).parent.joinpath("files", "dictionaries")
COMMAND_XML_PATH = DICTIONARIES_PATH.joinpath("command_banananation.xml")
CHANNEL_XML_PATH = DICTIONARIES_PATH.joinpath("channel_banananation.xml")
PARAMETER_XML_1_PATH = DICTIONARIES_PATH.joinpath(
    "parameter_banananation_1.xml")
PARAMETER_XML_2_PATH = DICTIONARIES_PATH.joinpath(
    "parameter_banananation_2.xml")
ADAPTATION_JS_PATH = DICTIONARIES_PATH.joinpath("adaptation.js")

ARTIFACTS_PATH.mkdir()


def assert_mission_version(dictionaries: List[DictionaryMetadata], id: int, mission: str, version: str) -> None:
    dict = next(filter(lambda d: d.id == id, dictionaries), None)
    assert dict is not None
    assert dict.mission == mission
    assert dict.version == version


def assert_deleted(dictionaries: List[DictionaryMetadata], id: int) -> bool:
    dict = next(filter(lambda d: d.id == id, dictionaries), None)
    return dict is None


def test_command_dictionary():
    with open(COMMAND_XML_PATH, "r") as fid:
        id = client.create_dictionary(fid.read())

    assert_mission_version(
        client.list_dictionaries()[DictionaryType.COMMAND], id, "Banana Nation", "1.0.0.0")

    client.delete_dictionary(id, DictionaryType.COMMAND)

    assert_deleted(
        client.list_dictionaries()[DictionaryType.COMMAND], id)


def test_channel_dictionary():
    with open(CHANNEL_XML_PATH, "r") as fid:
        id = client.create_dictionary(fid.read())

    assert_mission_version(
        client.list_dictionaries()[DictionaryType.CHANNEL], id, "Banana Nation", "1.0.0.0")

    client.delete_dictionary(id, DictionaryType.CHANNEL)

    assert_deleted(
        client.list_dictionaries()[DictionaryType.CHANNEL], id)


def test_parameter_dictionary():
    with open(PARAMETER_XML_1_PATH, "r") as fid:
        id = client.create_dictionary(fid.read())

    assert_mission_version(
        client.list_dictionaries()[DictionaryType.PARAMETER], id, "Banana Nation", "1.0.0.1")

    client.delete_dictionary(id, DictionaryType.PARAMETER)

    assert_deleted(
        client.list_dictionaries()[DictionaryType.PARAMETER], id)


def test_adaptation():
    with open(ADAPTATION_JS_PATH, "r") as fid:
        id = client.create_sequence_adaptation(fid.read())

    adaptations = client.list_sequence_adaptations()
    with open(ARTIFACTS_PATH.joinpath("test_list_adaptations.json"), "w") as fid:
        json.dump([i.to_dict() for i in adaptations], fid, indent=4)

    assert id in [a.id for a in adaptations]

    client.delete_sequence_adaptation(id)

    adaptations = client.list_sequence_adaptations()
    assert id not in [a.id for a in adaptations]


def test_parcels():
    # Set up
    with open(COMMAND_XML_PATH, "r") as fid:
        command_dictionary_id = client.create_dictionary(fid.read())
    with open(CHANNEL_XML_PATH, "r") as fid:
        channel_dictionary_id = client.create_dictionary(fid.read())
    with open(PARAMETER_XML_1_PATH, "r") as fid:
        parameter_dictionary_1_id = client.create_dictionary(fid.read())
    with open(PARAMETER_XML_2_PATH, "r") as fid:
        parameter_dictionary_2_id = client.create_dictionary(fid.read())
    with open(ADAPTATION_JS_PATH, "r") as fid:
        adaptation_id = client.create_sequence_adaptation(fid.read())

    # Create a parcel
    parcel = Parcel(
        "integration_test",
        command_dictionary_id,
        channel_dictionary_id,
        adaptation_id,
        [parameter_dictionary_1_id,
            parameter_dictionary_2_id]
    )
    parcel_id = client.create_parcel(parcel)

    # Assert parcel is as expected
    expected_parcel = Parcel(
        "integration_test",
        command_dictionary_id,
        channel_dictionary_id,
        adaptation_id,
        [parameter_dictionary_1_id,
            parameter_dictionary_2_id],
        parcel_id
    )
    created_parcel = next(
        filter(lambda p: p.id == parcel_id, client.list_parcels()), None)
    assert created_parcel is not None
    assert created_parcel == expected_parcel

    client.delete_parcel(parcel_id)

    # Parcel should now be deleted
    assert next(filter(lambda p: p.id == parcel_id,
                client.list_parcels()), None) is None

    # Cleanup
    client.delete_dictionary(command_dictionary_id, DictionaryType.COMMAND)
    client.delete_dictionary(channel_dictionary_id, DictionaryType.CHANNEL)
    client.delete_dictionary(parameter_dictionary_1_id,
                             DictionaryType.PARAMETER)
    client.delete_dictionary(parameter_dictionary_2_id,
                             DictionaryType.PARAMETER)
    client.delete_sequence_adaptation(adaptation_id)
