#!/usr/bin/env python3
"""
Log into Fronius Solarweb with the credentials in the environment (or .env),
get the data for the standard dayly plot of production, use, and battery level for the
previous day, and dump them to a timestamped JSON file.
"""

import argparse
import os
import json
import datetime as dt
from dotenv import load_dotenv

from fronius_scraper.fronius_session import FroniusSession


def scrape_daily_data(secrets: dict, date: dt.date) -> dict:
    """
    Use a login session to obtain the daily data chart for a given date as a serialized
    JSON dict.
    """
    fsession = FroniusSession(
        user=secrets["username"], password=secrets["password"], id=secrets["fronius-id"]
    )

    return json.dumps(fsession.get_chart(date=date))


def get_secrets_from_env() -> dict:
    """
    Obtain a dict of required secrets from the environment.
    """
    secrets = {
        "username": os.getenv("username"),
        "password": os.getenv("password"),
        "fronius-id": os.getenv("fronius-id"),
    }

    if None in secrets.values():
        none_secrets = ", ".join([x[0] for x in secrets.items() if x[1] is None])

        raise Exception(f"Fields {none_secrets} were not filled. Check your .env file.")

    return secrets


def run_scraper(output_dir: str = "./", days_ago: int = 1):
    load_dotenv()

    secrets = get_secrets_from_env()

    date_to_parse = dt.date.today() - dt.timedelta(days=days_ago)

    json_out = scrape_daily_data(secrets, date_to_parse)

    output_file = output_dir + date_to_parse.strftime("%Y%m%d.json")

    with open(output_file, "w") as outfile:
        outfile.write(json_out)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        "Fronius Solarweb Scraper",
        description=(
            "Scrape daily JSON generation & usage stats from Fronius Solarweb."
        ),
    )
    argparser.add_argument(
        "--output-dir",
        "-o",
        default="./",
        help="Where to put output files (default: %(default)s)",
    )
    argparser.add_argument(
        "--days-ago",
        "-n",
        default=1,
        help=(
            "The data of how many days ago should be scraped (default: %(default)s). "
            "Note that for non-premium users only the previous two days are available, "
            "and that the current day contains incomplete data."
        ),
    )

    args = argparser.parse_args()

    run_scraper(**vars(args))
