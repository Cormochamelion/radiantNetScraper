from conftest import check_db

from radiant_net_scraper import data_parser


class TestParseJsonDataFromFileList:
    def test_success(self, json_test_files, tmp_path):
        """
        General test, check if all test files get read without error.
        """
        path_str = str(tmp_path)
        data_parser.parse_json_data_from_file_list(
            json_test_files, db_path=path_str + "/generation_and_usage.sqlite3"
        )

        expected_db_path = f"{path_str}/generation_and_usage.sqlite3"

        check_db(expected_db_path)
