# RadiantNet Scraper

Retrieval and storage of generation and usage data from Fronius Solarweb and
similar systems.

## Quick start

Make your credentials available for the app by either filling out the `.env`
file (see `.env-example` for which fields should be filled), or by adding
a configuration file at either the site-wide or user specific config dir.
Use `radiant-net-paths` to see where that is on your platform. Alternatively,
you can also manually set `username`, `password`, and `fronius-id` in your
shell.

Currently, the `.env` method only works for Docker with the command outlined
below, while the other methods only work for the command line interfaces.

### Venv

Install the package in a virtual env (the `setup.sh` script can do that for
you).

You can then interactively use `radiant-net-scraper` to scrape a specific day,
`radiant-net-parser` to parse data from scraped JSON files into a database,
`radiant-net-paths` to display all the paths the app uses to look for things,
or `radiant-net-run` to start continually scraping data.

### Docker

There is a Dockerfile available for this package. First, ensure you have a
filled out `.env` file (see above). Then, start a container continually scraping
SolarWeb like this:

```sh
docker build -t rn-scraper . && \
    docker run -it --rm --env-file=.env rn-scraper rn-scraper
```
