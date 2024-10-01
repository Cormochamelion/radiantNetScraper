#!/usr/bin/env python3
import argparse
from radiant_net_scraper.scrape import run_scraper


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
