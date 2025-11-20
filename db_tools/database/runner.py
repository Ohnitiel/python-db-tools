import hashlib
import pickle
from concurrent.futures._base import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy.sql._elements_constructors import text

from .manager import DBConnectionManager
from ..logger import get_logger


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
            ignore_cache: Whether to ignore the cache.
            no_cache: Whether to not use the cache.
            **kwargs: Additional keyword arguments to pass to the file export function.
        """
        self.logger = get_logger(__name__)

        super().__init__(environment, connections)
        self.max_workers = max_workers
        self.save_path = save_path
        self.file_format = file_format
        self.kwargs = kwargs

    def _cache_query_result(
        self: "DBConnectionRunner",
        query: str,
        df: pd.DataFrame,
        failed_extractions: dict,
        run_hash: str,
    ):
        cache_root = f".cache/{run_hash}"

        df.to_parquet(f"{cache_root}.parquet")
        with open(f"{cache_root}.pkl", "wb") as f:
            pickle.dump(failed_extractions, f)

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
            self.logger.error(f"{connection} - Failed: {e}")
            return {"success": False, "error": e}

    def execute_query_multi_db(
        self: "DBConnectionRunner",
        query: str,
        commit: bool = False,
        parallel: bool = True,
        add_connection_column: bool = True,
        connection_column_name: str = "connection",
        no_cache: bool = False,
        ignore_cache: bool = False,
        ) -> pd.DataFrame:
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
        if not ignore_cache:
            run_hash = hashlib.sha256(
                f"{query}{','.join(self.connections)}".encode()
            ).hexdigest()
            cache_root = f".cache/{run_hash}"
            Path(f"{cache_root}.parquet").parent.mkdir(parents=True, exist_ok=True)

            if Path(f"{cache_root}.parquet").exists():
                answer = input("Encontrado cache. Deseja utilizá-lo?")
                if answer.lower() == "s":
                    return pd.read_parquet(f"{cache_root}.parquet")

        data = {}
        failed_extractions = {}
        if parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_results = {}
                for connection, config in self.connections.items():
                    future = executor.submit(
                        self.execute_query, query, connection, commit
                    )
                    future_results[future] = config["name"]

                for future in as_completed(future_results):
                    connection = future_results[future]
                    result = future.result()
                    data, failed_extractions = self._process_results(
                        result,
                        connection,
                        data,
                        failed_extractions,
                        connection_column_name,
                        add_connection_column,
                    )

        else:
            for connection, config in self.connections.items():
                result = self.execute_query(query, connection, commit)
                data, failed_extractions = self._process_results(
                    result,
                    connection,
                    data,
                    failed_extractions,
                    connection_column_name,
                    add_connection_column,
                )

        df = pd.concat(data, ignore_index=True)

        if not no_cache:
            run_hash = hashlib.sha256(
                f"{query}{','.join(self.connections)}".encode()
            ).hexdigest()
            self._cache_query_result(query, df, failed_extractions, run_hash)

        return df

    def _process_results(
        self: "DBConnectionRunner",
        result: dict[Any, Any],
        connection: str,
        data: dict[str, pd.DataFrame],
        failed_extractions: dict[Any, Any],
        connection_column_name: str,
        add_connection_column: bool = True,
    ) -> tuple[dict, dict]:
        if result["success"]:
            self.logger.info(f"{connection} - sucess!")
            data[connection] = pd.DataFrame(result["data"], columns=result["columns"])
            if add_connection_column:
                data[connection][connection_column_name] = connection
        else:
            failed_extractions[connection] = result["error"]

        return data, failed_extractions



if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    d = DBConnectionRunner("staging")
    print(d.connections)
