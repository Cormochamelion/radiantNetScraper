import sys

from test_infra.common_test_infra import check_db, json_test_file_dir, json_test_files

from radiant_net_scraper import scripts


class TestShowAppPaths:
    def test_success(self, monkeypatch):
        """
        Simply run the command, check that it doesn't crash.
        """
        args = ["TESTING"]

        monkeypatch.setattr(sys, "argv", args)
        scripts.show_app_paths()


class TestParseJsonFiles:
    def test_dir_input(self, monkeypatch, tmp_path):
        """
        Test that basic ingestion of the test JSON files works.
        """
        db_path = f"{str(tmp_path)}/db.sqlite3"

        args = ["TESTING", "--input-dir", json_test_file_dir(), "--output-db", db_path]

        monkeypatch.setattr(sys, "argv", args)

        scripts.parse_json_files()

        check_db(db_path)

    def test_file_list_input(self, monkeypatch, tmp_path):
        """
        Test that basic ingestion of the test JSON files works.
        """
        db_path = f"{str(tmp_path)}/db.sqlite3"
        args = [
            "TESTING",
            "--input-files",
            *json_test_files(),
            "--output-db",
            db_path,
        ]

        monkeypatch.setattr(sys, "argv", args)

        scripts.parse_json_files()

        check_db(db_path)
