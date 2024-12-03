"""
Manage the App's correspondence with Fronius Solarweb.
"""

import re
from bs4 import BeautifulSoup as bs
import urllib.parse as ulparse
import requests as rq

from radiant_net_scraper.config import get_configured_logger, get_fronius_secrets

LOGGER = get_configured_logger(__name__)


class _FroniusSession:
    """Class resonsible for managing the entire correspondence with fronius."""

    landing_url = "https://www.solarweb.com/"
    login_url = "https://www.solarweb.com/Account/ExternalLogin"
    login_form_post_url = "https://login.fronius.com/commonauth"
    chart_url = "https://www.solarweb.com/Chart/GetChartNew"
    key_pattern = re.compile(r"(?<=&sessionDataKey=)[a-z0-9\-]*")

    def __init__(self, user, password, fronius_id):
        self.session = rq.Session()
        self.key_pattern = re.compile(r"(?<=&sessionDataKey=)[a-z0-9\-]*")
        self.session_key = None
        self.secret = {"username": user, "password": password, "id": fronius_id}

        LOGGER.info("Logging into Fronius Solarweb at %s...", self.landing_url)
        self.login()
        LOGGER.info("... done logging in.")

    def is_logged_in(self) -> bool:
        """
        Check whether the session is logged in by requesting the landing page.
        When the request is redirected to the page of the personal PV system, everything
        is fine.
        """
        landig_page_resp = self.session.get(url=self.landing_url)

        landig_page_resp.raise_for_status()

        if len(landig_page_resp.history) < 2:
            # We didn't get forwarded to the PV page.
            return False

        try:
            query = ulparse.urlparse(landig_page_resp.url).query
            page_pv = query.split("=")[1]

        except Exception as e:
            raise ValueError(
                f"Can't parse out PV system ID from URL {landig_page_resp.url}. "
                "Something may have gone wrong with the login."
            ) from e

        return page_pv == self.secret["id"]

    def login(self):
        """Get all necessary data and cookies to perform all operations."""

        # Just to get the __RequestVerificationToken
        LOGGER.debug(
            "Getting request verification token by visiting the landing page at %s...",
            self.landing_url,
        )
        _ = self.session.get(url=self.landing_url)

        try:
            LOGGER.debug("Attempting to retrieve log-in page at %s...", self.login_url)
            login_page_resp = self.session.get(self.login_url, allow_redirects=True)
            login_page_resp.raise_for_status()

        except rq.ConnectionError as e:
            raise ValueError(
                f"Error getting Solarweb login page at {self.login_url}: {e}\n"
                f"Is the network ok, is {self.landing_url} reachable?"
            ) from e

        except rq.HTTPError as e:
            raise ValueError(
                f"Error getting Solarweb login page at {self.login_url}: {e}"
            ) from e

        session_key_match = re.search(self.key_pattern, login_page_resp.text)

        if not session_key_match:
            raise ValueError(
                "Couldn't extract session key from login response. Perhaps the login"
                "procedure has been changed by fronius?"
            )

        else:
            self.session_key = session_key_match.group()

        LOGGER.debug(
            "Filling and submitting login form to %s...", self.login_form_post_url
        )

        login_form_resp = self.session.post(
            url=self.login_form_post_url,
            data={
                "username": self.secret["username"],
                "password": self.secret["password"],
                "sessionDataKey": self.session_key,
            },
        )

        LOGGER.debug("Checking if they let us in...")

        callback_url = ulparse.parse_qs(ulparse.urlparse(login_page_resp.url).query)[
            "redirect_uri"
        ][0]

        login_soup = bs(login_form_resp.content, "lxml")

        login_params = {
            "code": None,
            "id_token": None,
            "state": None,
            "AuthenticatedIdPs": None,
            "session_state": None,
        }

        try:
            for key in login_params:
                login_params[key] = login_soup.find("input", {"name": key}).get("value")

        except AttributeError as e:
            # If those keys are not present, something went wrong with the login.
            raise ValueError(
                f"Error during login attempt: {e}. Are the credentials correct?"
            ) from e

        LOGGER.debug(
            "Seems the credentials checked out, getting cookies from login callback "
            "URL..."
        )
        # We only care about getting the cookies.
        _ = self.session.post(url=callback_url, data=login_params)

        if self.is_logged_in():
            LOGGER.info("Login successfull!")
        else:
            raise ValueError(
                "Something went wrong during the last phase of the login. "
                "Has something changed at Solarweb?"
            )

    def chart_data(self, fronius_id, date, view: str = "production") -> dict:
        """
        Construct a dict of values needed to retrieve the daily generation & usage chart
        from fronius. Use `view` to specify either "production" or "consumption".
        """
        return {
            "pvSystemId": fronius_id,
            "year": date.year,
            "month": date.month,
            "day": date.day,
            "interval": "day",
            "view": view,
        }

    def get_chart(self, date, chart_type: str = "production") -> dict:
        """
        Retrieve the daily generation & usage chart from fronius. See `chart_data` for
        values of `chart_type`.
        """
        LOGGER.debug(
            "Retrieving daily %s statistics data from %s...",
            chart_type,
            self.chart_url,
        )

        chart_resp = self.session.get(
            url=self.chart_url,
            data=self.chart_data(
                fronius_id=self.secret["id"], date=date, view=chart_type
            ),
        )

        # TODO Add handling of case that chart_resp doesn't contain json.
        return chart_resp.json()


class FroniusSession:
    """
    Singleton wrapper around the Fronius session to always have a single, pre-config'd
    session.
    """

    _session = None

    @classmethod
    def get_session(cls):
        """
        Getter for the single session object.
        """
        if cls._session is None:
            secrets = get_fronius_secrets()

            cls._session = _FroniusSession(
                user=secrets["username"],
                password=secrets["password"],
                fronius_id=secrets["fronius-id"],
            )

        return cls._session
