import re
from bs4 import BeautifulSoup as bs
import urllib.parse as ulparse
import requests as rq


class FroniusSession:
    """Class resonsible for managing the entire correspondence with fronius."""

    landing_url = "https://www.solarweb.com/"
    login_url = "https://www.solarweb.com/Account/ExternalLogin"
    login_form_post_url = "https://login.fronius.com/commonauth"
    chart_url = "https://www.solarweb.com/Chart/GetChartNew"
    key_pattern = re.compile("(?<=&sessionDataKey=)[a-z0-9\-]*")

    def __init__(self, user, password, id):
        self.session = rq.Session()
        self.key_pattern = re.compile("(?<=&sessionDataKey=)[a-z0-9\-]*")
        self.session_key = None
        self.is_logged_in = False
        self.secret = {"username": user, "password": password, "id": id}

        self.login()

    def login(self):
        """Get all necessary data and cookies to perform all operations."""

        # Just to get the __RequestVerificationToken
        _ = self.session.get(url=self.landing_url)

        try:
            login_page_resp = self.session.get(self.login_url, allow_redirects=True)
            login_page_resp.raise_for_status()

        except rq.ConnectionError as e:
            Exception(
                f"Error getting Solarweb login page at {self.login_url}: {e}\n"
                f"Is the network ok, is {self.landing_url} reachable?"
            )

        except rq.HTTPError as e:
            Exception(f"Error getting Solarweb login page at {self.login_url}: {e}")

        for line in login_page_resp.iter_lines():
            match = re.search(self.key_pattern, line.decode())
            if match:
                self.session_key = match.group()

        login_form_resp = self.session.post(
            url=self.login_form_post_url,
            data={
                "username": self.secret["username"],
                "password": self.secret["password"],
                "sessionDataKey": self.session_key,
            },
        )

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
            for key in login_params.keys():
                login_params[key] = login_soup.find("input", {"name": key}).get("value")

        except AttributeError:
            # If those keys are not present, something went wrong with the login.
            raise Exception(f"Error during login attempt. Are the credentials correct?")

        # We only care about getting the cookies.
        _ = self.session.post(url=callback_url, data=login_params)

        # FIXME Make this independent from the login fun, i.e. check if all
        # prerequisites are true.
        self.is_logged_in = True

    def chart_data(self, id, date):
        return {
            "pvSystemId": id,
            "year": date.year,
            "month": date.month,
            "day": date.day,
            "interval": "day",
            "view": "production",
        }

    def get_chart(self, date):
        chart_resp = self.session.get(
            url=self.chart_url, data=self.chart_data(id=self.secret["id"], date=date)
        )

        # TODO Add handling of case that chart_resp doesn't contain json.
        return chart_resp.json()
