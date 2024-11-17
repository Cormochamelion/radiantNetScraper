"""
Run the full flow of a day's scraping and ingestion into the database.
"""

from radiant_net_scraper.data_parser import parse_json_data_from_file_list
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

    output_file = run_scraper(**scraping_kwargs)
    parse_json_data_from_file_list([output_file], **parsing_kwargs)
