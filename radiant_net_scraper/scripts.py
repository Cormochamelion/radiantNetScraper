#!/usr/bin/env python3
import argparse
from radiant_net_scraper.scrape import run_scraper
from radiant_net_scraper import data_parser


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
        default="./",
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
    argparser = argparse.ArgumentParser(
        "fronius-parse-json-files",
        description=("Parse scraped JSON files into a usable format."),
    )

    argparser.add_argument(
        "--input-dir",
        "-i",
        default="./",
        type=str,
        # TODO Add info on filename pattern.
        help="Dir in which to search for JSON files to parse (default: %(default)s).",
    )

    argparser.add_argument(
        "--output-dir",
        "-o",
        default="./",
        type=str,
        # TODO Add info on what will be outputted.
        help="Dir to which output will be saved (default: %(default)s).",
    )

    args = argparser.parse_args()

    data_parser.main(output_dir=args.output_dir, input_dir=args.input_dir)
