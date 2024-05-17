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
    """
    Load required secrets and save the daily usage data to an output dir.
    """
    load_dotenv()

    secrets = get_secrets_from_env()

    date_to_parse = dt.date.today() - dt.timedelta(days=days_ago)

    json_out = scrape_daily_data(secrets, date_to_parse)

    output_file = output_dir + date_to_parse.strftime("%Y%m%d.json")

    with open(output_file, "w") as outfile:
        outfile.write(json_out)
