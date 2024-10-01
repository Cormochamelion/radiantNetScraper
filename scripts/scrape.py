#!/usr/bin/env python3
"""
Log into Fronius Solarweb with the credentials in the environment (or .env),
get the data for the standard dayly plot of production, use, and battery level for the
previous day, and dump them to a timestamped JSON file.
"""

from radiant_net_scraper.scripts import scrape

scrape()
