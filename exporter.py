from dotenv import load_dotenv

from lib.types import Struct
from manager import DBConnectionManager


class DBConnectionExporter(DBConnectionManager):
    def __init__(self: "DBConnectionExporter", connections: list[str] = []):
        super().__init__(connections)


if __name__ == "__main__":
    load_dotenv()
    d = DBConnectionExporter()
    print(d.connections)
