import os
import pytest

from dataclasses import astuple

from radiant_net_scraper import scrape


class TestRunScraper:
    def test_success(self, arbitrary_file_dummy_fronius_session, tmpdir):
        output_file_group = scrape.run_scraper(output_dir=f"{str(tmpdir)}/")

        assert all(os.path.exists(out_file) for out_file in astuple(output_file_group))

    @pytest.mark.requires_login
    def test_actual_retrieval(self, request, tmpdir):
        if "requires_login" not in request.config.getoption("-m", default=""):
            pytest.skip(
                "Requires login and will talk to Fronius. If credentials are set and"
                "this is ok, select with `pytest -m requires_login`."
            )

        output_file_group = scrape.run_scraper(output_dir=f"{str(tmpdir)}/")

        assert all(os.path.exists(out_file) for out_file in astuple(output_file_group))
