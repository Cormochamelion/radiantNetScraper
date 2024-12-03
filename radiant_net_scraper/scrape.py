"""
Retrieve data from a PV-System service provider.
"""

import json
import datetime as dt

from radiant_net_scraper.config import (
    get_chosen_raw_data_path,
    get_configured_logger,
)
from radiant_net_scraper.fronius_session import FroniusSession

LOGGER = get_configured_logger(__name__)


def scrape_daily_data(*get_chart_args, **get_chart_kwars) -> str:
    """
    Use a login session to obtain the daily data chart for a given date as a serialized
    JSON dict.
    """
    fsession = FroniusSession.get_session()

    return json.dumps(fsession.get_chart(*get_chart_args, **get_chart_kwars))


def save_chart_to_file(
    date: dt.date, output_dir: str, chart_type: str = "production"
) -> str:
    """
    Retrieve the chart data for a given date and type and save it to a JSON file.
    """
    LOGGER.info("Starting retrieval for day %s...", date)

    json_out = scrape_daily_data(date, chart_type)

    output_file = output_dir + date.strftime(f"%Y%m%d_{chart_type}.json")
    LOGGER.info("... done retrieving day %s, saving JSON to %s.", date, output_file)

    with open(output_file, "w", encoding="UTF-8") as outfile:
        outfile.write(json_out)

    return output_file


def run_scraper(output_dir: str | None = None, days_ago: int = 1) -> dict[str, str]:
    """
    Determine the date for which data should be retrieved and save the data for that
    date to disk.
    """
    if output_dir is None:
        output_dir = get_chosen_raw_data_path() + "/"

    date_to_parse = dt.date.today() - dt.timedelta(days=days_ago)

    chart_types = ("production", "consumption")

    output_files = {
        chart_type: save_chart_to_file(
            date=date_to_parse, output_dir=output_dir, chart_type=chart_type
        )
        for chart_type in chart_types
    }

    return output_files
