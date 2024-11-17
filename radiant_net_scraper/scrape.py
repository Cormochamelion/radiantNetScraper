"""
Retrieve data from a PV-System service provider.
"""

import json
import datetime as dt

from radiant_net_scraper.config import (
    Config,
    get_chosen_raw_data_path,
    get_config_paths,
)
from radiant_net_scraper.fronius_session import FroniusSession


def scrape_daily_data(secrets: dict, date: dt.date) -> dict:
    """
    Use a login session to obtain the daily data chart for a given date as a serialized
    JSON dict.
    """
    fsession = FroniusSession(
        user=secrets["username"], password=secrets["password"], id=secrets["fronius-id"]
    )

    return json.dumps(fsession.get_chart(date=date))


def get_fronius_secrets() -> dict:
    """
    Obtain a dict of required secrets for fronius, in this case from the config object.
    """
    config = Config.get_config()

    secrets = {
        "username": config["secrets"]["username"],
        "password": config["secrets"]["password"],
        "fronius-id": config["secrets"]["fronius-id"],
    }

    if None in secrets.values():
        none_secrets = ", ".join([x[0] for x in secrets.items() if x[1] is None])

        config_paths = get_config_paths()
        user_config = config_paths["user"]
        site_config = config_paths["site"]

        raise ValueError(
            f"Fields {none_secrets} were not filled. Ensure you set the secrets "
            f"either in the environment, the machine-wide config at {site_config}, or "
            f"your personal config at {user_config}."
        )

    return secrets


def run_scraper(output_dir: str | None = None, days_ago: int = 1):
    """
    Load required secrets and save the daily usage data to an output dir.
    """
    if output_dir is None:
        output_dir = get_chosen_raw_data_path() + "/"

    secrets = get_fronius_secrets()

    date_to_parse = dt.date.today() - dt.timedelta(days=days_ago)

    json_out = scrape_daily_data(secrets, date_to_parse)

    output_file = output_dir + date_to_parse.strftime("%Y%m%d.json")

    with open(output_file, "w", encoding="UTF-8") as outfile:
        outfile.write(json_out)
