import datetime as dt
import pandas as pd
import json
import os
import re


def parse_file(filepath: str) -> pd.DataFrame:
    """
    Parse a given JSON file representing the Fronius data for a given day into a
    data frame with columns corresponding to the types of data available and each
    row giving the time point of recording.
    """
    # TODO Validate againts a schema to detect if the format has changed.
    # TODO Handle IO errors
    with open(filepath) as infile:
        json_data = json.load(infile)

    # Check if the file contains data, or if it is too old and has been paywalled.
    if json_data["isPremiumFeature"]:
        # We can't extract any data, hence an empty df.
        return pd.DataFrame()

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

    # Create accessible datetime objects by converting milisecond count from time col
    # to POSIX second count.
    time_objs = [dt.datetime.fromtimestamp(timestamp / 1e3) for timestamp in time_col]

    usage_df = pd.DataFrame(data_cols)

    usage_df = usage_df.assign(
        year=[time_obj.year for time_obj in time_objs],
        month=[time_obj.month for time_obj in time_objs],
        day=[time_obj.day for time_obj in time_objs],
        hour=[time_obj.hour for time_obj in time_objs],
        minute=[time_obj.minute for time_obj in time_objs],
    )

    return usage_df


def is_daily_json_file(path: str) -> bool:
    """
    Check if a path points to a downloaded JSON file from the filename alone.
    """
    daily_json_re = re.compile(r"^[0-9]{8}\.json$")
    basename = os.path.basename(path)

    return os.path.isfile(path) and re.match(daily_json_re, basename) is not None


def get_json_list(dir: str) -> list[str]:
    """
    Find all the downloaded json files in a given dir and return them as a list.
    """
    paths = [os.path.join(dir, path) for path in os.listdir(dir)]
    return [*filter(is_daily_json_file, paths)]


def main():
    infilepaths = get_json_list(".")
    outfilepaths = map(lambda path: path[:-4] + "csv", infilepaths)

    for inpath, outpath in zip(infilepaths, outfilepaths):
        parse_file(inpath).to_csv(outpath)


if __name__ == "__main__":
    main()
