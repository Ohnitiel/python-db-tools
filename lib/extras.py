import tomllib
from pathlib import Path

from lib.types import Struct


def find_root_dir(markers: list[str]) -> Path:
    """
    Find the root directory of a project by searching for specific marker files or directories.

    This function traverses up the directory tree starting from the current working directory, looking for any of the specified marker items. It returns the first directory that contains at least one of the markers. If no markers are found, it raises a FileNotFoundError.

    Args:
        markers: A list of file or directory names to search for. These are typically project configuration files or directories that identify the project root (e.g., ['.git', 'pyproject.toml', 'requirements.txt']).

    Returns:
        Path: The first directory found that contains at least one of the specified markers.

    Raises:
        FileNotFoundError: If none of the specified markers are found in any parent directory up to the filesystem root.

    Example:
        >>> find_root_dir(['.git', 'pyproject.toml'])
        PosixPath('/home/user/my_project')

        >>> find_root_dir(['package.json', 'node_modules'])
        PosixPath('/home/user/web_project')

    Note:
        The search is case-sensitive and matches exact names. The function handles both Windows drive roots and Unix-style filesystem roots.
    """
    curr_path = Path(Path.cwd())
    drive = curr_path.drive
    root = Path("/")

    while True:
        if any(item.name in markers for item in curr_path.glob("*")):
            return curr_path
        curr_path = curr_path.parent
        if (curr_path == drive) or (curr_path.samefile(root)):
            markers_str = ", ".join(markers)
            raise FileNotFoundError(f"No marker found!\nMarkers: {markers_str}")


def get_available_connections() -> list[str]:
    """Return a list of available connection names from TOML files."""
    root = find_root_dir(["pyproject.toml"])
    config_path = root / ".config/config.toml"
    with open(config_path, "rb") as f:
        configs = Struct(tomllib.load(f))

    connections_path = config_path.parent / configs.paths.connections
    connections_path_list = list(connections_path.glob("*.toml"))

    return [x.stem for x in connections_path_list]
