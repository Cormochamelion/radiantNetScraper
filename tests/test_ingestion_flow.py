import os

from radiant_net_scraper import ingestion_flow


class TestIngestDay:
    def test_success(self, arbitrary_file_dummy_fronius_session, tmpdir):
        ingestion_flow.ingest_day(
            scraping_kwargs={"output_dir": f"{str(tmpdir)}/"},
            parsing_kwargs={"db_path": str(tmpdir) + "/generation_and_usage.sqlite3"},
        )
