import datetime as dt
import pandas as pd
import json
import os
import re

# Disallow in-place modification of dataframes.
pd.options.mode.copy_on_write = True


def parse_usage_json(usage_json: dict) -> pd.DataFrame:
    """
    Parse JSON dict representing the Fronius data for a given day into a
    data frame with columns corresponding to the types of data available and each
    row giving the time point of recording.
    """
    # Check if the file contains data, or if it is too old and has been paywalled.
    if usage_json["isPremiumFeature"]:
        # We can't extract any data, hence an empty df.
        return pd.DataFrame()

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

    return parse_usage_json(json_data)


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


def main(input_dir: str = "./", output_dir: str = "./"):
    infilepaths = get_json_list(input_dir)
    filenames = [os.path.basename(path) for path in infilepaths]

    outfilepaths = [
        *map(lambda filename: output_dir + filename[:-4] + "csv", filenames)
    ]

    df_list = [parse_file(inpath) for inpath in infilepaths]

    for df, outpath in zip(df_list, outfilepaths):
        df.to_csv(outpath, index=False)

    df_list_clean = [df for df in df_list if not df.empty]

    sum_dfs = [agg_daily_df(daily_df) for daily_df in df_list_clean]

    daily_agg_outdir = output_dir + "daily_aggregated"
    daily_agg_outpaths = [
        daily_agg_outdir + filename[:-4] + "csv" for filename in filenames
    ]

    for df, daily_agg_outpath in zip(sum_dfs, daily_agg_outpaths):
        df.to_csv(daily_agg_outpath, index=False)


if __name__ == "__main__":
    main()
