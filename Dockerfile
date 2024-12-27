FROM python:3.10.15-alpine3.20

WORKDIR /scraper

COPY radiant_net_scraper/ ./radiant_net_scraper
COPY pyproject.toml ./pyproject.toml

RUN pip3 install .

ENTRYPOINT ["radiant-net-run"]
