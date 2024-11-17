#!/usr/bin/env python3
"""
Wrappers around functions providing command line functionality with argument parsing
support.
"""
import argparse

from radiant_net_scraper.config import (
    get_chosen_data_path,
    get_chosen_raw_data_path,
    print_app_path_json,
)
from radiant_net_scraper.scrape import run_scraper
from radiant_net_scraper import data_parser


def show_app_paths():
    """
    Show under which paths the app expects certain things.
    """
    argparser = argparse.ArgumentParser(
        "RadiantNet Paths",
        description=(
            "Print a JSON formatted string showing at which paths the app expects "
            "certain things. Current fields are:"
            "`config`: Where config files are read from. "
            "`raw_data`: Where raw JSON files get saved to. "
            "`data`: Where the database for processed data lives."
        ),
    )

    argparser.parse_args()

    print_app_path_json()


def scrape():
    """
    Log into Fronius Solarweb with the credentials in the environment (or .env),
    get the data for the standard dayly plot of production, use, and battery level for the
    previous day, and dump them to a timestamped JSON file.
    """

    argparser = argparse.ArgumentParser(
        "RadiantNet Scraper",
        description=(
            "Scrape daily JSON generation & usage stats from Fronius Solarweb."
        ),
    )
    argparser.add_argument(
        "--output-dir",
        "-o",
        default=get_chosen_raw_data_path() + "/",
        help="Where to put output files (default: %(default)s)",
    )
    argparser.add_argument(
        "--days-ago",
        "-n",
        default=1,
        type=int,
        help=(
            "The data of how many days ago should be scraped (default: %(default)s). "
            "Note that for non-premium users only the previous two days are available, "
            "and that the current day contains incomplete data."
        ),
    )

    args = argparser.parse_args()

    run_scraper(**vars(args))


def parse_json_files():
    """
    Parse scraped JSON files into a usable format.
    """
    argparser = argparse.ArgumentParser(
        "RadiantNet Parser",
        description=("Parse scraped JSON files into a usable format."),
    )

    argparser.add_argument(
        "--input-dir",
        "-i",
        default="./",
        type=str,
        help=(
            "Dir in which to search for JSON files to parse (default: %(default)s). "
            "Files are assumed to be named in the format `YYYYMMDD.json`."
        ),
    )

    argparser.add_argument(
        "--input-files",
        help="List of input file paths. If provided, `--input-dir` is ignored.",
        nargs="+",
    )

    argparser.add_argument(
        "--output-db",
        "-o",
        default=get_chosen_data_path(),
        type=str,
        help="Dir to which the database will be saved (default: %(default)s).",
    )

    args = argparser.parse_args()

    if args.input_files:
        data_parser.parse_json_data_from_file_list(
            db_path=args.output_db, infiles=args.input_files
        )

    else:
        data_parser.parse_json_data(db_path=args.output_db, input_dir=args.input_dir)
