import datetime as dt
import pandas as pd
import json
import os
import re

from typing import NamedTuple, Iterable
from pipe import where, izip, Pipe
from pipe import map as pmap

# Disallow in-place modification of dataframes.
pd.options.mode.copy_on_write = True

class OutputDataFrames(NamedTuple):
    raw: pd.DataFrame
    aggregated: pd.DataFrame


@Pipe
def filter_by(x: Iterable, filter: Iterable[bool]) -> Iterable:
    """
    Filter `x` by the values of `filter`.
    """
    return zip(x, filter) | where(lambda x: x[1]) | pmap(lambda x: x[0])


def json_is_paywalled(usage_json: dict) -> bool:
    """
    Check if a downloaded JSON files is paywalled. If not, it should contain the data
    we are after.
    """
    return usage_json["isPremiumFeature"]


def parse_usage_json(usage_json: dict) -> pd.DataFrame:
    """
    Parse JSON dict representing the Fronius data for a given day into a
    data frame with columns corresponding to the types of data available and each
    row giving the time point of recording.
    """
    # Check if the file contains data, or if it is too old and has been paywalled.
    if json_is_paywalled(usage_json):
        raise ValueError(
            f"The usage dict is paywalled, can't extract any data from that."
        )

    data_series = usage_json["settings"]["series"]

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


def load_daily_usage_json(filepath: str) -> dict:
    """
    Load a json file containing daily usage data into a dict. Later validation should
    go in here.
    """
    # TODO Validate againts a schema to detect if the format has changed.
    # TODO Handle IO errors
    with open(filepath) as infile:
        return json.load(infile)


def agg_daily_df(
    daily_df: pd.DataFrame,
    sum_cols: list[str] = [
        "FromGenToBatt",
        "FromGenToGrid",
        "ToConsumer",
        "FromGenToConsumer",
    ],
    avg_cols: str = ["StateOfCharge"],
    time_cols: list[str] = ["year", "month", "day"],
) -> pd.DataFrame:
    """
    Sum all the usage / production data inside a daily  df.
    """
    sum_select_cols = [*set(time_cols) | set(sum_cols)]
    avg_select_cols = [*set(time_cols) | set(avg_cols)]

    sum_df = (
        daily_df[sum_select_cols].groupby(time_cols).aggregate("sum").add_prefix("sum_")
    )
    avg_df = (
        daily_df[avg_select_cols]
        .groupby(time_cols)
        .aggregate("mean")
        .add_prefix("mean_")
    )
    return pd.concat([sum_df, avg_df], axis=1).reset_index()


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


def process_daily_usage_dict(json_dict: dict) -> OutputDataFrames:
    """
    Process a json dict of daily usage data into a dataframe, and return it alongside
    a dataframe of the data aggregated over the whole day.
    """
    daily_df = parse_usage_json(json_dict)
    agg_df = agg_daily_df(daily_df)

    return OutputDataFrames(raw=daily_df, aggregated=agg_df)


def save_usage_dataframe_dict(
    output_dfs: OutputDataFrames, raw_df_outpath: str, agg_df_outpath: str
):
    """
    Save the dataframes in a dict for raw and aggregated data to their respective paths.
    """
    output_dfs.raw.to_csv(raw_df_outpath, index=False)
    output_dfs.aggregated.to_csv(agg_df_outpath, index=False)


def main(input_dir: str = "./", output_dir: str = "./"):
    infilepaths = get_json_list(input_dir)
    filenames = [os.path.basename(path) for path in infilepaths]

    usage_json_data = list(infilepaths | pmap(load_daily_usage_json))

    usage_json_contains_data = list(
        usage_json_data | pmap(lambda x: not json_is_paywalled(x))
    )

    filenames_clean = list(filenames | filter_by(usage_json_contains_data))

    raw_df_out_paths = [
        *map(lambda filename: output_dir + filename[:-4] + "csv", filenames_clean)
    ]

    daily_agg_outdir = output_dir + "daily_aggregated/"

    if not os.path.exists(daily_agg_outdir):
        os.mkdir(daily_agg_outdir)

    daily_agg_outpaths = [
        *map(lambda filename: daily_agg_outdir + filename[:-4] + "csv", filenames_clean)
    ]

    list(
        usage_json_data
        | filter_by(usage_json_contains_data)
        | pmap(process_daily_usage_dict)
        | izip(raw_df_out_paths, daily_agg_outpaths)
        | pmap(lambda x: save_usage_dataframe_dict(x[0], x[1], x[2]))
    )


if __name__ == "__main__":
    main()
