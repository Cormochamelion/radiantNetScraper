"""
Run the full flow of a day's scraping and ingestion into the database.
"""

from dataclasses import astuple
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler

from radiant_net_scraper.data_parser import parse_json_data_from_file_pair_list
from radiant_net_scraper.scrape import run_scraper


def ingest_day(
    scraping_kwargs: dict | None = None, parsing_kwargs: dict | None = None
) -> None:
    """
    Ingest the data from `days_ago`, save the raw data, and insert processed data
    into the app's DB.
    """
    scraping_kwargs = scraping_kwargs or {}
    parsing_kwargs = parsing_kwargs or {}

    output_files = run_scraper(**scraping_kwargs)
    parse_json_data_from_file_pair_list(list(astuple(output_files)), **parsing_kwargs)


def run_ingestion_continuously() -> None:
    """
    Use a scheduler to periodically run scraping and ingestion.
    """
    scheduler = BlockingScheduler()

    later = datetime.now() + timedelta(seconds=5)

    scheduler.add_job(ingest_day, trigger="interval", days=1, next_run_time=later)
    scheduler.start()
