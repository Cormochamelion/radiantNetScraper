import sqlite3

import pandas as pd


class Database:
    """
    Class for managing the SQLite DB for storing generation & usage data.
    """

    def __init__(
        self, db_dir: str = "./", db_filename: str = "generation_and_usage.sqlite3"
    ) -> None:
        # TODO Check if already exsting, if so inform user.
        db_path = db_dir + db_filename

        self.db_conn = sqlite3.connect(db_path)
        self.db_conn.row_factory = sqlite3.Row

        # Technically we don't need to create the table, pd.DataFrame.to_sql could do
        # the job for us. But I think it is sensible to create the tables beforehand
        # so errors get raised when there is a mismatch between columns.
        self._create_raw_data_table(self.db_conn.cursor())
        self._create_daily_agg_table(self.db_conn.cursor())

    def _create_table(
        self,
        db_cursor: sqlite3.Cursor,
        table_name: str,
        column_dict: dict[str, str],
        constraints: str,
    ) -> None:
        """
        Create a SQLite table from parameters.
        """
        columns = [" ".join([key, value]) for key, value in column_dict.items()]

        command_body = ", ".join(columns + constraints)

        command = f"CREATE TABLE IF NOT EXISTS {table_name} ({command_body})"

        db_cursor.execute(command)

    def _create_raw_data_table(self, db_cursor: sqlite3.Cursor) -> None:
        """
        Create the table containing raw data parsed from JSON files.
        """
        table_name = "raw_data"

        column_dict = {
            "FromGenToBatt": "REAL NOT NULL",
            "FromGenToGrid": "REAL NOT NULL",
            "ToConsumer": "REAL NOT NULL",
            "FromGenToConsumer": "REAL NOT NULL",
            "StateOfCharge": "REAL NOT NULL",
            "time": "INTEGER NOT NULL UNIQUE",
            "year": "INTEGER NOT NULL",
            "month": "INTEGER NOT NULL",
            "day": "INTEGER NOT NULL",
            "hour": "INTEGER NOT NULL",
            "minute": "INTEGER NOT NULL",
        }

        constraints = ["PRIMARY KEY (time)"]

        self._create_table(db_cursor, table_name, column_dict, constraints)

    def _create_daily_agg_table(self, db_cursor: sqlite3.Cursor) -> None:
        """
        Create the table containing data aggregated for each day.
        """
        table_name = "daily_aggregated"

        column_dict = {
            "sum_FromGenToBatt": "REAL NOT NULL",
            "sum_FromGenToGrid": "REAL NOT NULL",
            "sum_ToConsumer": "REAL NOT NULL",
            "sum_FromGenToConsumer": "REAL NOT NULL",
            "mean_StateOfCharge": "REAL NOT NULL",
            "year": "INTEGER NOT NULL",
            "month": "INTEGER NOT NULL",
            "day": "INTEGER NOT NULL",
        }

        constraints = ["PRIMARY KEY (year, month, day)"]

        self._create_table(db_cursor, table_name, column_dict, constraints)

    def _insert_df(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Insert a dataframe into the database.
        """
        df.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def insert_raw_data_df(self, raw_data_df: pd.DataFrame) -> None:
        """
        Insert data into the raw_data table.
        """
        self._insert_df(raw_data_df, "raw_data")

    def insert_daily_agg_df(self, daily_agg_df: pd.DataFrame) -> None:
        """
        Insert data into the  table.
        """
        self._insert_df(daily_agg_df, "daily_aggregated")
