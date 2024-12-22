from itertools import groupby
from dataclasses import astuple
import glob
import os
import re
import sqlite3

from radiant_net_scraper.types import ChartFileGroup


TABLE_QUERY = "select name from sqlite_master where type = 'table';"


def check_db(expected_db_path: str, expect_rows: bool = True) -> None:
    """
    Run checks to ensure the usage database at `expected_db_path` is as expected.
    """
    assert os.path.exists(expected_db_path)

    db_conn = sqlite3.connect(expected_db_path)
    db_cursor = db_conn.cursor()
    table_info = db_cursor.execute(TABLE_QUERY).fetchall()

    # Ensure the db has the right number of tables
    assert len(table_info) == 2

    # Ensure each table contains data.
    for table in table_info:
        table_name = table[0]
        table_n_entry_query = f"SELECT COUNT(1) FROM {table_name}"
        table_n_entry = db_cursor.execute(table_n_entry_query).fetchall()[0][0]

        if expect_rows:
            assert table_n_entry > 0


def json_test_file_dir() -> str:
    """
    Provide the path of the test data dir.
    """
    return f"{os.getcwd()}/tests/test_data"


def json_test_files() -> list[str]:
    """
    Provide a list of json test files date from the test data dir.
    """
    return sorted(glob.glob(f"{json_test_file_dir()}/*.json"))


def arbitrary_json_test_file() -> str:
    """
    Provide the paths to the JSON test files of an arbitrary group of generation and
    usage files.
    """
    return json_test_files()[0]


def json_test_file_groups() -> list[ChartFileGroup]:
    """
    Provide a list of groups of json test files belonging to one date from the test
    data dir.
    """
    all_files = sorted(glob.glob(f"{json_test_file_dir()}/*.json"))

    group_replace_re = re.compile(r"(_consumption|_production)")

    groupings = groupby(
        all_files,
        key=lambda file: re.sub(group_replace_re, "", file),
    )

    return [ChartFileGroup(*group) for _, group in groupings]


def arbitrary_json_test_group() -> ChartFileGroup | None:
    """
    Provide the paths to the JSON test files of an arbitrary group of generation and
    usage files.
    """
    for group in json_test_file_groups():
        if not any(file is None for file in astuple(group)):
            return group

    return None
