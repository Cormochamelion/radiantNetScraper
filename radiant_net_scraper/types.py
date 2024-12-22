"""
Assorted types used throughout the package.
"""

import pandas as pd

from dataclasses import dataclass
from typing import NamedTuple


class OutputDataFrames(NamedTuple):
    """
    Named tuple to keep a days data grouped together.
    """

    raw: pd.DataFrame
    aggregated: pd.DataFrame


@dataclass
class ChartFileGroup:
    """
    Bundle different types of chart files together.
    """

    production: str
    consumption: str | None = None


# FIXME Declare in greater detail what makes a chart.
Chart = dict


@dataclass
class ChartGroup:
    """
    Bundle different types of chart together.
    """

    production: Chart
    consumption: Chart | None = None


@dataclass
class ChartGroupData:
    """
    Bundle parsed data from a chart group.
    """

    production: OutputDataFrames
    consumption: OutputDataFrames | None = None
