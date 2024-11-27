import glob
import os
from pytest_cases import parametrize


class TestParseJsonDataFromFileListCases:

    class TestFileCases:
        @parametrize(
            "file",
            glob.glob(f"{os.getcwd()}/tests/test_data/*.json"),
            ids=os.path.basename,
        )
        def case_all_test_files(self, file):
            return file
