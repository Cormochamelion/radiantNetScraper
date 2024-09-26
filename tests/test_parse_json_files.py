import os
import sqlite3

from radiant_net_scraper import data_parser

TABLE_QUERY = "select name from sqlite_master where type = 'table';"


class TestParseJsonDataFromFileList:
    def test_success(self, json_test_files, tmp_path):
        """
        General test, check if all test files get read without error.
        """
        path_str = str(tmp_path)
        data_parser.parse_json_data_from_file_list(
            json_test_files, database_dir=path_str + "/"
        )

        expected_db_path = f"{path_str}/generation_and_usage.sqlite3"

        assert os.path.exists(expected_db_path)

        db_conn = sqlite3.connect(expected_db_path)
        db_cursor = db_conn.cursor()
        table_info = db_cursor.execute(TABLE_QUERY).fetchall()

        # Ensure the db has the right number of tables
        assert len(table_info) == 2
