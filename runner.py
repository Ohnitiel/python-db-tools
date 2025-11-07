from pathlib import Path

from dotenv import load_dotenv

from manager import DBConnectionManager


class DBConnectionRunner(DBConnectionManager):
    def __init__(self: "DBConnectionRunner", connections: list[str] = []):
        super().__init__(connections)

    def execute_query(
        self: "DBConnectionRunner", query: str, connection: str, commit: bool = False
    ):
        pass

    def execute_query_multi_db(
        self: "DBConnectionRunner",
        query: str,
        commit: bool = False,
        parallel: bool = True,
        add_connection_column: bool = True,
        connection_column_name: str = "connection",
    ):
        if not parallel:
            pass
        pass

    def export_to_file(self: "DBConnectionRunner", save_path: Path):
        pass


if __name__ == "__main__":
    load_dotenv()
    d = DBConnectionRunner()
    print(d.connections)
