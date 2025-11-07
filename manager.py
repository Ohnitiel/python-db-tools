import os
import tomllib
from pathlib import Path
from typing import Any

from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.create import create_engine

from lib.extras import find_root_dir
from lib.types import Struct


class DBConnectionManager:
    configurations: Struct[Any]
    connections: Struct[Any]
    engines: Struct[Engine]

    def __init__(self: "DBConnectionManager", connections: list[str] = []):
        self.configurations = self._load_config()
        self.connections = self._get_gonnections()

        if connections:
            self._filter_connections(connections)

        for connection, config in self.connections.items():
            config.connstring = self._build_connstring(config)

        self.engines = self._create_engines()

    def _load_config(self: "DBConnectionManager") -> Struct:
        root: Path = find_root_dir(["pyproject.toml"])
        config_path: Path = root / ".config/config.toml"

        with open(config_path, "rb") as f:
            configurations = Struct(tomllib.load(f))

        configurations.paths = {
            config: config_path.parent / path
            for config, path in configurations.paths.items()
        }

        return configurations

    def _get_gonnections(self: "DBConnectionManager") -> Struct:
        config_path: Path = self.configurations.paths.connections

        connections = Struct()
        for connection_path in config_path.glob("*.toml"):
            with open(connection_path, "rb") as f:
                connection = Struct(tomllib.load(f))

            connections.update(connection)

        for connection, information in connections.items():
            for key, value in information.items():
                if key == "password" and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    information[key] = os.environ[env_var]

        return connections

    def _filter_connections(self: "DBConnectionManager", connections: list[str]):
        self.connections = Struct(
            {
                key: value
                for key, value in self.connections.items()
                if key in connections
            }
        )

    def _build_connstring(self: "DBConnectionManager", config: Struct) -> str:
        db_type = config.type
        host = config.host
        port = config.port
        database = config.database
        username = config.username
        password = config.password
        connection = f"{username}:{password}@{host}:{port}/{database}"

        if db_type == "postgresql":
            return f"postgresql+psycopg2://{connection}"
        else:
            raise NotImplementedError(f"Connection type '{db_type}' not implemented!")

    def _create_engines(self: "DBConnectionManager") -> Struct:
        engines = Struct()
        for connection, config in self.connections.items():
            engines[connection] = create_engine(config.connstring)

        return engines

    def close_all(self: "DBConnectionManager"):
        for engine in self.engines.values():
            engine.dispose()

        self.engines.clear()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    d = DBConnectionManager()
    print(len(d.connections))
    d.close_all()
