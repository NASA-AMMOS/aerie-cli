from typing import Dict
import pytest
import requests

from aerie_cli.aerie_host import AerieHost, COMPATIBLE_AERIE_VERSIONS


class MockResponse:
    def __init__(self, json: Dict, text: str, ok: bool) -> None:
        self.json_data = json
        self.text = text
        self.ok = ok

    def json(self) -> Dict:
        if self.json_data is None:
            raise requests.exceptions.JSONDecodeError("", "", 0)
        return self.json_data


class MockSession:

    def __init__(self, mock_response: MockResponse) -> None:
        self.mock_response = mock_response

    def get(self, *args, **kwargs) -> MockResponse:
        return self.mock_response

    def post(self, *args, **kwargs) -> MockResponse:
        return self.mock_response


def get_mock_aerie_host(json: Dict = None, text: str = None, ok: bool = True) -> AerieHost:
    mock_response = MockResponse(json, text, ok)
    mock_session = MockSession(mock_response)
    return AerieHost("", "", mock_session)


def test_check_aerie_version():
    aerie_host = get_mock_aerie_host(
        json={"version": COMPATIBLE_AERIE_VERSIONS[0]})

    aerie_host.check_aerie_version()


def test_check_invalid_version():
    aerie_host = get_mock_aerie_host(json={"version": "1.0.0"})

    with pytest.raises(RuntimeError) as e:
        aerie_host.check_aerie_version()

    assert "Incompatible Aerie version: 1.0.0" in str(e.value)


def test_no_version_endpoint():
    aerie_host = get_mock_aerie_host(text="blah Aerie Gateway blah", ok=True)

    with pytest.raises(RuntimeError) as e:
        aerie_host.check_aerie_version()

    assert "Unknown Aerie host version" in str(e.value)


def test_version_broken_gateway():
    aerie_host = get_mock_aerie_host(
        text="502 Bad Gateway or something", ok=True)

    with pytest.raises(RuntimeError) as e:
        aerie_host.check_aerie_version()

    assert "Bad response from Aerie Gateway" in str(e.value)
