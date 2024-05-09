import pandas as pd
import json


def parse_file(filepath: str) -> pd.DataFrame:
    """
    Parse a given JSON file representing the Fronius data for a given day into a
    data frame with columns corresponding to the types of data available and each
    row giving the time point of recording.
    """
    # TODO Handle IO errors
    with open(filepath) as infile:
        json_data = json.load(infile)

    data_series = json_data["settings"]["series"]

    series_data = {
        series["id"]: series["data"]
        for series in data_series
        # BattOperatingState has len 1, so it can't be part of the df.
        if series["id"] != "BattOperatingState"
    }

    # The series data comes in a list of lists the latter of which is always len 2,
    # what here is called a cell. Each cell contains the timestamp in Unix time in
    # its first element, and the series value in the second.
    first_series = next(iter(series_data.values()))
    time_col = [cell[0] for cell in first_series]
    data_cols = {
        series_id: [cell[1] for cell in data] for series_id, data in series_data.items()
    }

    data_cols["time"] = time_col

    return pd.DataFrame(data_cols)


def main():
    parse_file("20240508.json")


if __name__ == "__main__":
    main()
