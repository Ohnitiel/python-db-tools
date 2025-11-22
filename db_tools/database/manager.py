import os
import tomllib
import urllib.parse
from pathlib import Path
from typing import Any

from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.create import create_engine

from ..extras import find_root_dir, Struct
from ..logger import get_logger



class DBConnectionManager:
    """
    Manages database connections.
    """

    configurations: Struct[Any]
    connections: Struct[Any]
    engines: Struct[Engine]

    def __init__(
        self: "DBConnectionManager", environment: str, connections: list[str] = []
    ):
        """
        Initializes a new DBConnectionManager object.

        Args:
            connections: A list of connection names to manage.
        """
        self.logger = get_logger(__name__)
        self.configurations = self._load_config()
        self.connections = self._get_gonnections()

        if connections:
            self._filter_connections(connections)

        self.logger.info(f"Initialized manager for {len(self.connections)} connecions")

        for connection, config in self.connections.items():
            config.connstring = self._build_connstring(config, environment)

        self.engines = self._create_engines()

    def _load_config(self: "DBConnectionManager") -> Struct:
        """
        Loads the configuration from the config.toml file.

        Returns:
            A Struct object containing the configuration.
        """
        root: Path = find_root_dir(["pyproject.toml"])
        config_path: Path = root / "config/config.toml"

        with open(config_path, "rb") as f:
            configurations = Struct(tomllib.load(f))

        configurations.paths = {
            config: config_path.parent / path
            for config, path in configurations.paths.items()
        }

        return configurations

    def _get_gonnections(self: "DBConnectionManager") -> Struct:
        """
        Gets the database connections from the config/database/connections directory.

        Returns:
            A Struct object containing the database connections.
        """
        config_path: Path = self.configurations.paths.connections

        connections = Struct()
        for connection_path in config_path.glob("*.toml"):
            with open(connection_path, "rb") as f:
                connection = Struct(tomllib.load(f))

            connections.update(connection.connections)

        for connection, information in connections.items():
            connections[connection] = self._resolve_passwords(information)

        return connections

    def _resolve_passwords(self: "DBConnectionManager", info: Any):
        """
        Recursively resolves password using env vars.

        Args:
            info: Database connection object
        """
        if isinstance(info, dict):
            return Struct({k: self._resolve_passwords(v) for k, v in info.items()})
        elif isinstance(info, str) and info.startswith("${") and info.endswith("}"):
            env_var = info[2:-1]
            return urllib.parse.quote(os.environ[env_var])
        return info

    def _filter_connections(self: "DBConnectionManager", connections: list[str]):
        """
        Filters the connections to only include the ones specified in the connections list.

        Args:
            connections: A list of connection names to keep.
        """
        self.connections = Struct(
            {
                key: value
                for key, value in self.connections.items()
                if key in connections
            }
        )

    def _build_connstring(
        self: "DBConnectionManager", config: Struct, environment: str
    ) -> str:
        """
        Builds a connection string from a configuration Struct.

        Args:
            config: A Struct object containing the connection configuration.

        Returns:
            A connection string.
        """
        db_type = config.type
        if db_type == "postgresql":
            conn_string = "postgresql+psycopg://"
        else:
            raise NotImplementedError(f"Connection type '{db_type}' not implemented!")

        host = config[environment].host
        port = config.port
        database = config.database
        username = getattr(config[environment], "username", config.get("username"))
        password = getattr(config[environment], "password", config.get("password"))
        connection = f"{username}:{password}@{host}:{port}/{database}"

        return conn_string + connection

    def _create_engines(self: "DBConnectionManager") -> Struct:
        """
        Creates SQLAlchemy engines for all the connections.

        Returns:
            A Struct object containing the SQLAlchemy engines.
        """
        engines = Struct()
        for connection, config in self.connections.items():
            engines[connection] = create_engine(config.connstring)

        self.logger.info(f"Created engines for {len(self.connections)} connections")

        return engines

    def close_all(self: "DBConnectionManager"):
        """
        Closes all the database connections.
        """
        for engine in self.engines.values():
            engine.dispose()

        self.logger.info("Disposed of all configured engines")

        self.engines.clear()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    d = DBConnectionManager("staging")
    print(len(d.connections))
    d.close_all()
