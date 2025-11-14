from concurrent.futures._base import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy.sql._elements_constructors import text

from manager import DBConnectionManager


class DBConnectionRunner(DBConnectionManager):
    """
    Runs queries on multiple database connections.
    """

    max_workers: int
    save_path: Optional[Path]
    file_format: Optional[str]
    kwargs: dict

    def __init__(
        self: "DBConnectionRunner",
        environment: str,
        connections: list[str] = [],
        max_workers: int = 8,
        save_path: Optional[Path] = None,
        file_format: Optional[str] = None,
        **kwargs,
    ):
        """
        Initializes a new DBConnectionRunner object.

        Args:
            connections: A list of connection names to run queries on.
            max_workers: The maximum number of threads to use.
            save_path: The path to save the results to.
            file_format: The format to save the results in.
            **kwargs: Additional keyword arguments to pass to the file export function.
        """
        super().__init__(environment, connections)
        self.max_workers = max_workers
        self.save_path = save_path
        self.file_format = file_format
        self.kwargs = kwargs

    def execute_query(
        self: "DBConnectionRunner", query: str, connection: str, commit: bool = False
    ) -> dict[str, Any]:
        """
        Executes a query on a single database connection.

        Args:
            query: The query to execute.
            connection: The name of the connection to execute the query on.
            commit: Whether to commit the transaction.

        Returns:
            A dictionary containing the results of the query.
        """
        try:
            with self.engines[connection].connect() as conn:
                cursor = conn.execute(text(query))

                result = cursor.fetchall()
                columns = cursor.keys()

                if commit:
                    conn.commit()
                else:
                    conn.rollback()

            return {"success": True, "data": result, "columns": columns}
        except Exception as e:
            return {"success": False, "error": e}

    def execute_query_multi_db(
        self: "DBConnectionRunner",
        query: str,
        commit: bool = False,
        parallel: bool = True,
        add_connection_column: bool = True,
        connection_column_name: str = "connection",
    ) -> tuple[pd.DataFrame, dict]:
        """
        Executes a query on multiple database connections.

        Args:
            query: The query to execute.
            commit: Whether to commit the transaction.
            parallel: Whether to execute the queries in parallel.
            add_connection_column: Whether to add a column with the connection name to the results.
            connection_column_name: The name of the connection column.

        Returns:
            A tuple containing a DataFrame with the results and a dictionary with any errors that occurred.
        """
        data = {}
        failed_extractions = {}
        if not parallel:
            for connection, config in self.connections.items():
                result = self.execute_query(query, connection, commit)
                if result["success"]:
                    data[config["name"]] = pd.DataFrame(
                        result["data"], columns=result["columns"]
                    )
                else:
                    failed_extractions[config["name"]] = result["error"]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = {}
            for connection, config in self.connections.items():
                future = executor.submit(self.execute_query, query, connection, commit)
                future_results[future] = config["name"]

            for future in as_completed(future_results):
                connection = future_results[future]
                result = future.result()

                if result["success"]:
                    data[connection] = pd.DataFrame(
                        result["data"], columns=result["columns"]
                    )
                else:
                    failed_extractions[connection] = result["error"]

        df = pd.concat(data, ignore_index=True)

        if self.save_path is not None:
            self.export_to_file(df, self.save_path, self.file_format, **self.kwargs)

        return df, failed_extractions

    def export_to_file(
        self: "DBConnectionRunner",
        df: pd.DataFrame,
        save_path: Path,
        format: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Exports a DataFrame to a file.

        Args:
            df: The DataFrame to export.
            save_path: The path to save the file to.
            format: The format to save the file in.
            **kwargs: Additional keyword arguments to pass to the file export function.
        """
        if format is None:
            format = save_path.suffix.lstrip(".")

        # TODO handle other formats (csv, json)
        if format == "xlsx":
            # TODO Handle max sheet size rows and/or columns
            df.to_excel(save_path, engine="openpyxl", index=False)
        elif format == "parquet":
            df.to_parquet(save_path, engine="pyarrow", index=False)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    d = DBConnectionRunner("staging")
    print(d.connections)
