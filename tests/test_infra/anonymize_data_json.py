#!/usr/bin/env python3

import datetime
import json
import random

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


def anonymize_series_data(series: list[dict], timestamp_diff: int) -> list[dict]:
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
                if type(cell[i]) is not str:
                    cell[i] = round(cell[i] * random_data_factor, 2)

    return series


def anonymize_data_json(infile: str, outfile: str) -> None:
    """
    Replace actual user data in a file with plausible random data.
    """
    with open(infile, "r") as input:
        json_dict = json.load(input)

    actual_date = datetime.datetime.strptime(json_dict["title"], DATE_FORMAT)
    spoofed_date = random_date()

    anon_dict = json_dict

    anon_dict["title"] = spoofed_date.strftime(DATE_FORMAT)
    random_sum_val = str(round(random.random() * 1000, 2)).replace(".", ",")
    anon_dict["sumValue"] = f"{random_sum_val} kWh"
    anon_dict["settings"]["sumValue"] = f"{random_sum_val} kWh"

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
    anon_dict["settings"]["series"] = anonymize_series_data(
        anon_dict["settings"]["series"], date_diff
    )

    with open(outfile, "w") as output:
        json.dump(anon_dict, output, indent=2)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser("anonymize-data-json")
    parser.add_argument(
        "--infile", "-i", help="Input JSON file", type=str, required=True
    )
    parser.add_argument(
        "--outfile", "-o", help="Output JSON file", type=str, required=True
    )

    args = parser.parse_args()

    anonymize_data_json(args.infile, args.outfile)
