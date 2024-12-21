import os
import pytest
from pytest_cases import parametrize

from test_infra.common_test_infra import check_db, json_test_files

from radiant_net_scraper import data_parser


class TestParseJsonDataFromFileList:
    @pytest.mark.filterwarnings("error")
    def test_success(self, tmp_path):
        """
        General test, check if all test files get read without error.
        """
        path_str = str(tmp_path)
        data_parser.parse_json_data_from_file_list(
            json_test_files(), db_path=path_str + "/generation_and_usage.sqlite3"
        )

        expected_db_path = f"{path_str}/generation_and_usage.sqlite3"

        check_db(expected_db_path)

    @parametrize(
        "file",
        json_test_files(),
        ids=os.path.basename,
    )
    @pytest.mark.filterwarnings("error")
    def test_files(self, tmp_path, file):
        """
        Test each file individually, mainly if ingestion runs without issues.
        """
        path_str = str(tmp_path)
        data_parser.parse_json_data_from_file_list(
            [file], db_path=path_str + "/generation_and_usage.sqlite3"
        )

        expected_db_path = f"{path_str}/generation_and_usage.sqlite3"

        # Rows are already checked in the full ingest test, some test files don't
        # contain data, on those no rows is actually expected.
        check_db(expected_db_path, expect_rows=False)
