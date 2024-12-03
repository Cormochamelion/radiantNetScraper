"""
Assorted types used throughout the package.
"""

import pandas as pd
from typing import NamedTuple


class OutputDataFrames(NamedTuple):
    """
    Named tuple to keep a days data grouped together.
    """

    raw: pd.DataFrame
    aggregated: pd.DataFrame
