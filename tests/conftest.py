from json import load
import os
from pytest_cases import fixture
import re

import radiant_net_scraper.fronius_session as fsession
from radiant_net_scraper.fronius_session import _FroniusSession
from test_infra.common_test_infra import arbitrary_json_test_group


@fixture
def arbitrary_file_dummy_fronius_session(monkeypatch) -> None:
    """
    Monkeypatch FroniusSession to not do any requests, and just return the
    contents of an arbitrary test JSON file when asked for a chart.
    """
    dummy_secrets = {"username": "dummy", "password": "dummy", "fronius-id": "dummy"}

    monkeypatch.setattr(fsession, "get_fronius_secrets", lambda: dummy_secrets)

    arbitrary_chart_pair = {}
    chart_type_re = re.compile(r"_(consumption|production).json")

    for infile in arbitrary_json_test_group():
        chart_type_match = re.search(chart_type_re, os.path.basename(infile))

        if not chart_type_match:
            raise ValueError(f"Couldn't determine chart_type from file {infile}.")

        chart_type = chart_type_match.groups()[0]
        chart_data = load(open(infile, encoding="UTF-8"))

        arbitrary_chart_pair[chart_type] = chart_data

    monkeypatch.setattr(_FroniusSession, "login", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        _FroniusSession,
        "get_chart",
        lambda self, date, chart_type: arbitrary_chart_pair[chart_type],
    )

    return None
