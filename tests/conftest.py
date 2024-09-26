import os
import glob

from pytest_cases import fixture


@fixture
def json_test_files() -> list[str]:
    """
    Provide a list of json test files from the test data dir.
    """
    test_data_path: str = f"{os.getcwd()}/tests/test_data"
    return glob.glob(f"{test_data_path}/*.json")
