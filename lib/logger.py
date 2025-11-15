import logging
import logging.config
import tomllib
from pathlib import Path

from lib.extras import find_root_dir


def setup_logging():
    try:
        config_path = find_root_dir(["pyproject.toml"]) / ".config/logging/config.toml"
        with open(config_path, "rb") as f:
            config_dict = tomllib.load(f)

        for handler, config in config_dict["handlers"].items():
            if "filename" in config:
                Path(config["filename"]).parent.mkdir(parents=True, exist_ok=True)

        logging.config.dictConfig(config_dict)
        logging.info("Log configuration loaded from TOML file")

    except FileNotFoundError:
        logging.basicConfig(
            level=logging.WARNING,
            format=("%(asctime)s - %(levelname)s - %(message)s"),
        )
        logging.warning("Logger configuration not found. Using default.")


def get_logger(name) -> logging.Logger:
    return logging.getLogger(name)
