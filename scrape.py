#!/usr/bin/env python3
"""
Log into Fronius Solarweb with the credentials in the environment (or .env),
get the data for the standard dayly plot of production, use, and battery level for the
previous day, and dump them to a timestamped JSON file.
"""

import os
import json
import datetime as dt
from dotenv import load_dotenv

from fronius_scraper.fronius_session import FroniusSession


def main():
    load_dotenv()

    secrets = {
        "username": os.getenv("username"),
        "password": os.getenv("password"),
        "fronius-id": os.getenv("fronius-id"),
    }

    if None in secrets.values():
        none_secrets = ", ".join([x[0] for x in secrets.items() if x[1] is None])

        raise Exception(
            f"Fields {none_secrets} where not filled. Check your .env " f"file."
        )

    fsession = FroniusSession(
        user=secrets["username"], password=secrets["password"], id=secrets["fronius-id"]
    )

    yesterday = dt.date.today() - dt.timedelta(days=1)

    json_out = json.dumps(fsession.get_chart(date=yesterday))

    output_dir = "./"
    output_file = output_dir + yesterday.strftime("%Y%m%d.json")

    with open(output_file, "w") as outfile:
        outfile.write(json_out)


if __name__ == "__main__":
    main()
