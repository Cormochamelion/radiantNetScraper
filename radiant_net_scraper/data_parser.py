"""
Parse generation & usage JSON files into dataframes and insert them into the apps
database.
"""

import datetime as dt
import numpy as np
import pandas as pd
import json
import os
import re

from functools import reduce
from typing import NamedTuple, Iterable
from pipe import where, Pipe
from pipe import map as pmap

from radiant_net_scraper.config import get_chosen_data_path
from radiant_net_scraper.database import Database

# Disallow in-place modification of dataframes.
pd.options.mode.copy_on_write = True

# TODO Add option to add to database right after retrieving a json file.


class OutputDataFrames(NamedTuple):
    """
    Named tuple to keep a days data grouped together.
    """

    raw: pd.DataFrame
    aggregated: pd.DataFrame


@Pipe
def filter_by(x: Iterable, flags: Iterable[bool]) -> Iterable:
    """
    Filter `x` by the values of `flags`, keeping values in `x` if the value in `flags`
    at the same position is truthy.
    """
    return zip(x, flags) | where(lambda x: x[1]) | pmap(lambda x: x[0])


def json_is_paywalled(usage_json: dict) -> bool:
    """
    Check if a downloaded JSON files is paywalled. If not, it should contain the data
    we are after.
    """
    return usage_json["isPremiumFeature"]


def series_data_to_df(series_data: list[list[int,]]) -> pd.DataFrame:
    """
    Convert an individual data series containing timestamp & value to a dataframe.

    The series data comes in a list of lists the latter of which is always len 2,
    what here is called a cell. Each cell contains the timestamp in Unix time in
    its first element, and the series value in the second. This function constructs
    a data frame constiting of a time and value column from that.
    """
    time_arr = np.empty((len(series_data)), np.int64)
    data_arr = np.empty((len(series_data)), type(series_data[0][1]))

    for i, cell in enumerate(series_data):
        time_arr[i] = cell[0]
        data_arr[i] = cell[1]

    return pd.DataFrame({"time": time_arr, "data": data_arr})


def parse_usage_json(usage_json: dict) -> pd.DataFrame:
    """
    Parse JSON dict representing the Fronius data for a given day into a
    data frame with columns corresponding to the types of data available and each
    row giving the time point of recording.
    """
    # Check if the file contains data, or if it is too old and has been paywalled.
    if json_is_paywalled(usage_json):
        raise ValueError(
            "The usage dict is paywalled, can't extract any data from that."
        )

    data_series = usage_json["settings"]["series"]

    series_data = {
        series["id"]: series["data"]
        for series in data_series
        # BattOperatingState has len 1, so it can't be part of the df.
        if series["id"] not in ["BattOperatingState"]
    }

    series_dfs = []
    for series_id, series_values in series_data.items():
        series_df = series_data_to_df(series_values)
        series_dfs.append(series_df.rename(columns={"data": series_id}))

    usage_df = reduce(lambda x, y: pd.merge(x, y, how="outer", on="time"), series_dfs)

    time_objs = [
        dt.datetime.fromtimestamp(timestamp / 1e3) for timestamp in usage_df.time
    ]

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
    with open(filepath, encoding="UTF-8") as infile:
        return json.load(infile)


def agg_daily_df(
    daily_df: pd.DataFrame,
    sum_cols: list[str] = (
        "FromGenToBatt",
        "FromGenToGrid",
        "ToConsumer",
        "FromGenToConsumer",
    ),
    avg_cols: list[str] = ("StateOfCharge"),
    time_cols: list[str] = ("year", "month", "day"),
) -> pd.DataFrame:
    """
    Sum all the usage / production data inside a daily  df.
    """
    present_cols = set(daily_df.columns.values)
    sum_select_cols = [*(set(time_cols) | set(sum_cols)) & present_cols]
    avg_select_cols = [*(set(time_cols) | set(avg_cols)) & present_cols]

    time_cols = list(time_cols)

    sum_df = daily_df[sum_select_cols].groupby(time_cols).agg("sum").add_prefix("sum_")
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


def get_json_list(input_dir: str) -> list[str]:
    """
    Find all the downloaded json files in a given dir and return them as a list.
    """
    paths = [os.path.join(input_dir, path) for path in os.listdir(input_dir)]
    return [*filter(is_daily_json_file, paths)]


def process_daily_usage_dict(json_dict: dict) -> OutputDataFrames:
    """
    Process a json dict of daily usage data into a dataframe, and return it alongside
    a dataframe of the data aggregated over the whole day.
    """
    daily_df = parse_usage_json(json_dict)
    agg_df = agg_daily_df(daily_df)

    return OutputDataFrames(raw=daily_df, aggregated=agg_df)


def save_usage_dataframe_dict(output_dfs: OutputDataFrames, db_handler: Database):
    """
    Save the dataframes in a dict for raw and aggregated data into the DB.
    """
    db_handler.insert_raw_data_df(output_dfs.raw)
    db_handler.insert_daily_agg_df(output_dfs.aggregated)


def parse_json_data_from_file_list(infiles: list[str], **kwargs) -> None:
    """
    Parse a list of JSON files into the SQLite DB.
    """
    if "db_path" not in kwargs:
        kwargs["db_path"] = get_chosen_data_path()
    db_handler = Database(**kwargs)

    list(
        infiles
        | pmap(load_daily_usage_json)
        | where(lambda x: not json_is_paywalled(x))
        | pmap(process_daily_usage_dict)
        | pmap(lambda x: save_usage_dataframe_dict(x, db_handler))
    )


def parse_json_data(input_dir: str = "./", **kwargs):
    """
    Parse all the json files in `input_dir` into a sqlite DB.
    """
    infilepaths = get_json_list(input_dir)
    parse_json_data_from_file_list(infilepaths, **kwargs)
