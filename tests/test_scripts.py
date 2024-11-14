import sys

from radiant_net_scraper import scripts


class TestParseJsonFiles:
    def test_dir_input(self, monkeypatch, tmp_path, json_test_file_dir):
        """
        Test that basic ingestion of the test JSON files works.
        """
        db_path = f"{str(tmp_path)}/db.sqlite3"

        args = ["TESTING", "--input-dir", json_test_file_dir, "--output-db", db_path]

        monkeypatch.setattr(sys, "argv", args)

        scripts.parse_json_files()

    def test_file_list_input(self, monkeypatch, tmp_path, json_test_files):
        """
        Test that basic ingestion of the test JSON files works.
        """
        db_path = f"{str(tmp_path)}/db.sqlite3"
        args = ["TESTING", "--input-files", *json_test_files, "--output-db", db_path]

        monkeypatch.setattr(sys, "argv", args)

        scripts.parse_json_files()
