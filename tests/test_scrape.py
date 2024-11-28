import os
import pytest

from radiant_net_scraper import scrape


class TestRunScraper:
    def test_success(self, arbitrary_file_dummy_fronius_session, tmpdir):
        out_files = scrape.run_scraper(output_dir=f"{str(tmpdir)}/")

        assert all(os.path.exists(out_file) for out_file in out_files.values())

    @pytest.mark.requires_login
    def test_actual_retrieval(self, request, tmpdir):
        if "requires_login" not in request.config.getoption("-m", default=""):
            pytest.skip(
                "Requires login and will talk to Fronius. If credentials are set and"
                "this is ok, select with `pytest -m requires_login`."
            )

        out_files = scrape.run_scraper(output_dir=f"{str(tmpdir)}/")

        assert all(os.path.exists(out_file) for out_file in out_files.values())
