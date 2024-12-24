"""
Parse generation & usage JSON files into dataframes and insert them into the apps
database.
"""

import datetime as dt
import numpy as np
import pandas as pd
import glob
import json
import re

from dataclasses import asdict, astuple
from functools import reduce
from itertools import groupby
from typing import Iterable
from pipe import where, Pipe
from pipe import map as pmap

from radiant_net_scraper.config import get_chosen_data_path, get_configured_logger
from radiant_net_scraper.database import Database
from radiant_net_scraper.types import (
    ChartFileGroup,
    ChartGroup,
    ChartGroupData,
    OutputDataFrames,
)

LOGGER = get_configured_logger(__name__)


@Pipe
def filter_by(x: Iterable, flags: Iterable[bool]) -> Iterable:
    """
    Filter `x` by the values of `flags`, keeping values in `x` if the value in `flags`
    at the same position is truthy.
    """
    return zip(x, flags) | where(lambda x: x[1]) | pmap(lambda x: x[0])


@Pipe
def run_pipe(x: Iterable) -> None:
    """
    Run a pipe for its side effects, discard output.
    """
    list(x)


def json_is_paywalled(usage_json: dict) -> bool:
    """
    Check if a downloaded JSON files is paywalled. If not, it should contain the data
    we are after.
    """
    return usage_json["isPremiumFeature"]


def group_is_paywalled(group: ChartGroup) -> bool:
    """
    Check if any of the charts in a group is paywalled.
    """
    return any(
        json_is_paywalled(chart) for chart in astuple(group) if chart is not None
    )


def timestamp_to_posix(timestamp) -> int:
    """
    Convert the fronius timestamp to POSIX time in seconds.
    """
    return timestamp / 1e3


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
        dt.datetime.fromtimestamp(timestamp_to_posix(timestamp))
        for timestamp in usage_df.time
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
    LOGGER.debug("Loading file at %s...", filepath)
    with open(filepath, encoding="UTF-8") as infile:
        return json.load(infile)


def load_chart_group(group: ChartFileGroup) -> ChartGroup:
    """
    Load the files from a ChartFileGroup into a ChartGroup.
    """
    return ChartGroup(
        **{
            name: load_daily_usage_json(file)
            for name, file in asdict(group).items()
            if file is not None
        }
    )


def calculate_col_kwh(raw_df=pd.DataFrame, agg_cols=list[str]) -> float:
    """
    Calulate the work in kWh on each time step for a set of columns.
    """
    indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=2)

    raw_df["time_step"] = (
        raw_df["time"]
        .rolling(window=indexer)
        .apply(
            lambda sub_series: timestamp_to_posix(sub_series.iloc[1])
            - timestamp_to_posix(sub_series.iloc[0])
        )
        # I'm assuming the last value is the same as the previous one. This is a
        # compromise between assuming all values are the same and saying it's impossible
        # to know the last value.
        .ffill()
        # Convert seconds to hours.
        .apply(lambda seconds: seconds / (60**2))
    )

    for col_name in agg_cols:
        raw_df[col_name] = (raw_df["time_step"] * raw_df[col_name]) / 1e3

    return raw_df


def agg_daily_df(
    daily_df: pd.DataFrame,
    kwh_cols: tuple[str, ...],
    avg_cols: tuple[str, ...],
    time_cols: tuple[str, ...],
) -> pd.DataFrame:
    """
    Sum all the usage / production data inside a daily  df.
    """
    present_cols = set(daily_df.columns.values)
    kwh_select_cols = [*(set(time_cols) | set(kwh_cols)) & present_cols]
    avg_select_cols = [*(set(time_cols) | set(avg_cols)) & present_cols]

    # To group this needs to be a list.
    time_col_list = list(time_cols)

    kwh_raw_df = calculate_col_kwh(
        daily_df[[*(set(["time"]) | set(kwh_select_cols))]], kwh_cols
    )

    kwh_df = (
        kwh_raw_df[kwh_select_cols].groupby(time_col_list).agg("sum").add_prefix("kwh_")
    )
    avg_df = (
        daily_df[avg_select_cols]
        .groupby(time_col_list)
        .aggregate("mean")
        .add_prefix("mean_")
    )
    return pd.concat([kwh_df, avg_df], axis=1).reset_index()


def get_json_list(input_dir: str) -> list[str]:
    """
    Find all the downloaded json files in a given dir and return them as a list.
    """
    return glob.glob(f"{input_dir}/*.json")


def get_chart_file_groups(files: list[str]) -> list[ChartFileGroup]:
    """
    Figure out which files in a list belong to the same date, and return a list of file
    groups.
    """
    group_replace_re = re.compile(r"(_consumption|_production)")

    groupings = groupby(
        sorted(files),
        key=lambda file: re.sub(group_replace_re, "", file),
    )

    return [ChartFileGroup(*group) for _, group in groupings]


def summarize_daily_df(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize a daily production / usage df by computing total work & avg battery soc.
    """
    kwh_col_re = re.compile(r"^[A-Z]")

    avg_cols = tuple(["StateOfCharge"])

    kwh_cols = tuple(
        [
            col
            for col in daily_df.columns
            if re.search(kwh_col_re, col) is not None and col not in avg_cols
        ]
    )

    time_cols = ("year", "month", "day")

    return agg_daily_df(
        daily_df, time_cols=time_cols, avg_cols=avg_cols, kwh_cols=kwh_cols
    )


def process_daily_usage_dict(json_dict: dict) -> OutputDataFrames:
    """
    Process a json dict of daily usage data into a dataframe, and return it alongside
    a dataframe of the data aggregated over the whole day.
    """
    daily_df = parse_usage_json(json_dict)

    return OutputDataFrames(raw=daily_df, aggregated=summarize_daily_df(daily_df))


def interpolate_consumption_from_production(
    production_data: OutputDataFrames,
) -> OutputDataFrames:
    """
    Use production data to interpolate consumption values where possible.
    """
    prod_raw = production_data.raw.copy()

    from_gen_cols = set(
        [
            "FromGenToBatt",
            "FromGenToGrid",
            "FromGenToConsumer",
            "FromGenToSomewhere",
            "FromGenToWattPilot",
        ]
    )

    use_from_gen_cols = set(prod_raw) & from_gen_cols

    if use_from_gen_cols:
        prod_raw["FromGen"] = prod_raw.apply(
            lambda row: sum(row[col] for col in use_from_gen_cols), 1
        )

    prod_raw = prod_raw.drop(labels=list(from_gen_cols), axis=1, errors="ignore")

    return OutputDataFrames(prod_raw, summarize_daily_df(prod_raw))


def parse_chart_group_data(group: ChartGroup) -> ChartGroupData:
    """
    Parse data from chart group.
    """
    return ChartGroupData(
        **{
            name: process_daily_usage_dict(chart)
            for name, chart in asdict(group).items()
            if chart is not None
        }
    )


def save_usage_dataframe_dict(output_dfs: OutputDataFrames, db_handler: Database):
    """
    Save the dataframes in a dict for raw and aggregated data into the DB.
    """
    db_handler.insert_raw_data_df(output_dfs.raw)
    db_handler.insert_daily_agg_df(output_dfs.aggregated)


def merge_chart_data(
    dfs_a: OutputDataFrames, dfs_b: OutputDataFrames
) -> OutputDataFrames:
    """
    Merge two sets of output data by merging their respective data frames.
    """
    return OutputDataFrames(*[pd.merge(df_a, df_b) for df_a, df_b in zip(dfs_a, dfs_b)])


def save_chart_data(group: ChartGroupData, *args, **kwargs) -> None:
    """
    Merge the parsed data of a group and insert it into the DB.
    """
    group_data_filtered = [data for data in astuple(group) if data]

    merged_data = reduce(merge_chart_data, group_data_filtered)

    save_usage_dataframe_dict(merged_data, *args, **kwargs)


def parse_json_data_from_file_pair_list(
    infile_groups: list[ChartFileGroup], **kwargs
) -> None:
    """
    Parse a list of JSON file groups into the SQLite DB.
    """
    if "db_path" not in kwargs:
        kwargs["db_path"] = get_chosen_data_path()
    db_handler = Database(**kwargs)

    _ = (
        infile_groups
        | pmap(load_chart_group)
        | where(lambda x: not group_is_paywalled(x))
        | pmap(parse_chart_group_data)
        | pmap(lambda x: save_chart_data(x, db_handler))
        | run_pipe()
    )


def parse_json_data_from_file_list(infiles: list[str], **kwargs) -> None:
    """
    Parse a list of JSON files into the SQLite DB.
    """
    parse_json_data_from_file_pair_list(get_chart_file_groups(infiles), **kwargs)


def parse_json_data(input_dir: str = "./", **kwargs):
    """
    Parse all the json files in `input_dir` into a sqlite DB.
    """
    LOGGER.info("Finding file groups to ingest in %s...", input_dir)
    file_groups = get_chart_file_groups(get_json_list(input_dir))

    LOGGER.debug("Groups to be ingested: %s", file_groups)

    parse_json_data_from_file_pair_list(file_groups, **kwargs)
