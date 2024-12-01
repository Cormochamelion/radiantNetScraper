#!/usr/bin/env python3

from copy import deepcopy
import datetime
import json
import pandas as pd
import random
import re

from radiant_net_scraper.data_parser import series_data_to_df, timestamp_to_posix

DATE_FORMAT = r"%d.%m.%Y"
# Conversion factor for seconds to the fronius timestamp.
TIMESTAMP_SECONDS_FACTOR = 1000


def random_date(
    start: datetime.date = datetime.date(1970, 1, 1),
    stop: datetime.date = datetime.date.today(),
) -> datetime.date:
    """
    Generate a random date bewteen start and stop date inclusively.
    """
    n_days = stop - start
    random_dist = random.randint(0, n_days.days)
    return start + datetime.timedelta(random_dist)


def anonymize_series_data(series: list[dict], timestamp_diff: int):
    """
    Move series timestamps by `timestamp_diff` and jiggle the date around a bit.
    """
    # Use random factor between 0.5 & 1.5 (range of lenght 1.5, minimum of 0.5).
    random_data_factor = random.random() + 0.5
    for data_series in series:
        for cell in data_series["data"]:
            # Modify cell in place.
            cell[0] = cell[0] + timestamp_diff

            # Add random data factor to remaining cell elements
            for i in range(1, len(cell)):
                # FIXME Sure up this type checking.
                if not isinstance(cell[i], str):
                    cell[i] = round(cell[i] * random_data_factor, 2)


def calculate_series_kwh(series: dict) -> float:
    """
    Calculate the amount of kwH in a series. Errors if the series does not contain
    power data.
    """
    unit = series["yAxis"]
    if not unit == "W":
        raise ValueError(
            f"Series does not contain power data, unit is {unit}, not 'W'."
        )

    series_df = series_data_to_df(series_data=series["data"])

    indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=2)

    series_df["time_step"] = (
        series_df["time"]
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

    return sum(series_df["time_step"] * series_df["data"]) / 1e3


def calculate_daily_kwh(series_data=list[dict], id_pattern=r"^FromGen") -> float:
    """
    Calulate the sum value of all series where the ids match a pattern.
    """
    selected_series_daily_kwh = [
        calculate_series_kwh(series)
        for series in series_data
        if re.search(id_pattern, series["id"])
    ]

    total_daily_kwh = sum(selected_series_daily_kwh)

    return round(total_daily_kwh, 2)


def anonymize_data_json(
    infile: str, outfile: str, spoofed_date: datetime.date = random_date()
) -> None:
    """
    Replace actual user data in a file with plausible random data.
    """
    with open(infile, "r") as input:
        json_dict = json.load(input)

    actual_date = datetime.datetime.strptime(json_dict["title"], DATE_FORMAT)

    anon_dict = deepcopy(json_dict)

    anon_dict["title"] = spoofed_date.strftime(DATE_FORMAT)

    time_start = datetime.datetime(
        spoofed_date.year, spoofed_date.month, spoofed_date.day
    )
    time_stop = datetime.datetime(
        spoofed_date.year, spoofed_date.month, spoofed_date.day, 23, 55
    )

    anon_dict["settings"]["xAxis"]["max"] = (
        time_stop.timestamp() * TIMESTAMP_SECONDS_FACTOR
    )
    anon_dict["settings"]["xAxis"]["min"] = (
        time_start.timestamp() * TIMESTAMP_SECONDS_FACTOR
    )

    # Difference on the scale of the timestamp between actual and fictional date.
    date_diff = (time_start - actual_date).total_seconds() * TIMESTAMP_SECONDS_FACTOR

    anonymize_series_data(anon_dict["settings"]["series"], date_diff)

    new_sum_val = calculate_daily_kwh(json_dict["settings"]["series"])
    anon_dict["sumValue"] = f"{new_sum_val} kWh"
    anon_dict["settings"]["sumValue"] = f"{new_sum_val} kWh"

    with open(outfile, "w") as output:
        json.dump(anon_dict, output, indent=2)


def anonymize_multiple_files(infiles: list[str], outfiles: list[str]):
    """
    Anonymize multiple JSON files, keeping their dates sequential.
    """
    if not len(infiles) == len(outfiles):
        raise ValueError("`infiles` and `outfiles` need to have the same length.")

    for infile, outfile in zip(infiles, outfiles):
        anonymize_data_json(infile, outfile)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser("anonymize-data-json")
    parser.add_argument(
        "--infiles", "-i", help="Input JSON files", type=str, required=True, nargs="+"
    )
    parser.add_argument(
        "--outfiles", "-o", help="Output JSON files", type=str, required=True, nargs="+"
    )

    args = parser.parse_args()

    anonymize_multiple_files(args.infiles, args.outfiles)
