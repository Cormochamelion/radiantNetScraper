from json import load
from pytest_cases import fixture

import radiant_net_scraper.fronius_session as fsession
from radiant_net_scraper.fronius_session import _FroniusSession
from test_infra.common_test_infra import arbitrary_json_test_file


@fixture
def arbitrary_file_dummy_fronius_session(monkeypatch) -> None:
    """
    Monkeypatch FroniusSession to not do any requests, and just return the
    contents of an arbitrary test JSON file when asked for a chart.
    """
    dummy_secrets = {"username": "dummy", "password": "dummy", "fronius-id": "dummy"}

    monkeypatch.setattr(fsession, "get_fronius_secrets", lambda: dummy_secrets)

    with open(arbitrary_json_test_file(), encoding="UTF-8") as infile:
        source_json_data = load(infile)

    monkeypatch.setattr(_FroniusSession, "login", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        _FroniusSession, "get_chart", lambda *args, **kwargs: source_json_data
    )

    return None
