import pytest

from aerie_cli.client import AerieClient

@pytest.mark.parametrize(["server_url","gql_url"],[
    (
        "localhost", 
        "localhost:8080/v1/graphql"
    ),
    (
        "http://localhost", 
        "http://localhost:8080/v1/graphql"
    ),
    (
        "eurcdevaerieX.jpl.nasa.gov", 
        "eurcdevaerieX.jpl.nasa.gov:8080/v1/graphql"
    ),
    (
        "http://eurcdevaerieX.jpl.nasa.gov",
        "http://eurcdevaerieX.jpl.nasa.gov:8080/v1/graphql"
    ),
    (
        "https://aerie-ui.eurc-whatever.jpl.nasa.gov",
        "https://aerie-hasura.eurc-whatever.jpl.nasa.gov/v1/graphql"
    ),
    (
        "http://aerie-ui.eurc-whatever.jpl.nasa.gov",
        "http://aerie-hasura.eurc-whatever.jpl.nasa.gov/v1/graphql"
    ),
    (
        "https://aerie-ui.eurc-whatever.jpl.nasa.gov/",
        "https://aerie-hasura.eurc-whatever.jpl.nasa.gov/v1/graphql"
    )
])
def test_graphql_urls(server_url,gql_url):
    client = AerieClient(server_url)
    assert client.graphql_path() == gql_url

@pytest.mark.parametrize(["server_url","gateway_url"],[
    (
        "localhost", 
        "localhost:9000"
    ),
    (
        "http://localhost", 
        "http://localhost:9000"
    ),
    (
        "eurcdevaerieX.jpl.nasa.gov", 
        "eurcdevaerieX.jpl.nasa.gov:9000"
    ),
    (
        "http://eurcdevaerieX.jpl.nasa.gov",
        "http://eurcdevaerieX.jpl.nasa.gov:9000"
    ),
    (
        "https://aerie-ui.eurc-whatever.jpl.nasa.gov",
        "https://aerie-gateway.eurc-whatever.jpl.nasa.gov"
    ),
    (
        "http://aerie-ui.eurc-whatever.jpl.nasa.gov",
        "http://aerie-gateway.eurc-whatever.jpl.nasa.gov"
    ),
    (
        "https://aerie-ui.eurc-whatever.jpl.nasa.gov/",
        "https://aerie-gateway.eurc-whatever.jpl.nasa.gov"
    )
])
def test_gateway_urls(server_url,gateway_url):
    client = AerieClient(server_url)
    assert client.gateway_path() == gateway_url
