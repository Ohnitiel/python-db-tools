# GEMINI.md

This document provides a comprehensive overview of the `db_tools` project for future development and maintenance.

### Project Overview

*   **Purpose:** A Python-based tool for executing SQL queries across multiple database connections simultaneously, with both a Command-Line Interface (CLI) and a Graphical User Interface (GUI).
*   **Technologies:**
    *   **Backend:** Python
    *   **Database:** SQLAlchemy, psycopg2 (for PostgreSQL)
    *   **GUI:** customtkinter
    *   **CLI:** argparse
    *   **Data Handling:** pandas, openpyxl, pyarrow
*   **Dependencies:**
    *   `cryptography`
    *   `customtkinter`
    *   `openpyxl`
    *   `pandas`
    *   `psycopg[binary,pool]`
    *   `pyarrow`
    *   `python-dotenv`
    *   `sqlalchemy`
*   **Architecture:**
    *   The core logic resides in the `db_tools` package.
    *   `db_tools.database.manager.DBConnectionManager`: Manages database connection configurations. It reads connection details from `.toml` files located in the `.config/database/connections` directory.
    *   `db_tools.database.runner.DBConnectionRunner`: Executes queries using the `DBConnectionManager`. It supports parallel query execution via a thread pool and includes a caching mechanism for results.
    *   `db_tools.exporter.export_data`: Handles the exporting of data to various formats.
    *   `main.py`: Provides the CLI for the tool.
    *   `gui.py`: Provides a GUI using `customtkinter`.

### Building and Running

**Dependencies:**

The project's dependencies are listed in `pyproject.toml`. Install them using `uv`:

```bash
uv sync
```

**Configuration:**

1.  Create a `.env` file in the project's root directory to store database credentials and other environment variables.
2.  Define your database connections in `.toml` files within the `.config/database/connections/` directory. Passwords can be securely stored as environment variables and referenced in the configuration files using the `${ENV_VAR}` syntax.
3.  The main configuration file is `config/config.toml`, which points to other configuration files for the database, logging, and locales.

**Running the application:**

*   **CLI:**
    To see all available options, run:
    ```bash
    uv run main.py --help
    ```
    Example usage:
    ```bash
    uv run main.py -c connection1 connection2 -q "SELECT * FROM my_table;" --save-path "results.xlsx"
    ```

*   **GUI:**
    ```bash
    uv run gui.py
    ```

### Development Conventions

*   **Configuration:** The project uses `.toml` files for configuration, separating connection details from the main codebase.
*   **Structure:** The project is well-organized, with a clear separation of concerns between database logic, the CLI, and the GUI.
*   **Logging:** The application uses Python's built-in `logging` module.
*   **Error Handling:** The `DBConnectionRunner` includes error handling to gracefully manage failed queries.
*   **Concurrency:** The `ThreadPoolExecutor` is used to run queries in parallel for improved performance.
*   **Caching:** The project implements a file-based caching mechanism for query results to speed up repeated queries.
*   **Synchronization Strategy:** To keep the CLI and GUI in sync, follow these principles:
    *   **Enforce Separation of Concerns:** The core business logic should reside in the `db_tools` library and be completely independent of any UI.
    *   **UI-Agnostic Logic:** The `db_tools` library should not contain any UI-specific code. For user interactions, use callbacks that can be implemented by the respective UI.
    *   **Thin Frontends:** The `main.py` (CLI) and `gui.py` (GUI) should only be responsible for collecting user input and calling the `db_tools` library with the appropriate parameters.