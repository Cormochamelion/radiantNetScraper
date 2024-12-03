import os
from pytest_cases import parametrize

from test_infra.common_test_infra import check_db, json_test_file_groups

from radiant_net_scraper import data_parser


class TestParseJsonDataFromFileList:
    def test_success(self, tmp_path):
        """
        General test, check if all test files get read without error.
        """
        path_str = str(tmp_path)
        data_parser.parse_json_data_from_file_pair_list(
            json_test_file_groups(), db_path=path_str + "/generation_and_usage.sqlite3"
        )

        expected_db_path = f"{path_str}/generation_and_usage.sqlite3"

        check_db(expected_db_path)

    @parametrize(
        "file_pair",
        json_test_file_groups(),
        ids=lambda file_pair: os.path.basename(file_pair[0]),
    )
    def test_files(self, tmp_path, file_pair):
        """
        Test each file individually, mainly if ingestion runs without issues.
        """
        path_str = str(tmp_path)
        data_parser.parse_json_data_from_file_pair_list(
            [file_pair], db_path=path_str + "/generation_and_usage.sqlite3"
        )

        expected_db_path = f"{path_str}/generation_and_usage.sqlite3"

        # Rows are already checked in the full ingest test, some test files don't
        # contain data, on those no rows is actually expected.
        check_db(expected_db_path, expect_rows=False)
