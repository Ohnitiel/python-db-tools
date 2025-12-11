# DB Tools

A powerful Python tool for executing SQL queries across multiple database connections simultaneously. This tool is designed for data analysts, engineers, and developers who need to run the same query against multiple databases with identical schemas.

## Features

- **Multi-database support**: Connect to PostgreSQL, MySQL, SQL Server, SQLite, and Oracle databases
- **Parallel execution**: Run queries concurrently across multiple connections for faster results
- **Flexible output**: Export results to Excel, JSON, or CSV formats
- **Both CLI and GUI**: Command-line interface for automation and GUI for interactive use
- **Caching**: Built-in query result caching to speed up repeated queries
- **Configuration-based**: Manage database connections through configuration files

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd db-tools
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. You can run the application using uv:
   ```bash
   uv run main.py [options]
   # or
   uv run gui.py
   ```

4. Or install dependencies and run with pip:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Database Connections

Database connections are configured in `config/database/connections/` as TOML files. Create a new file for each connection:

```toml
[connections.my_postgres_db]
type = "postgresql"
database = "mydatabase"
port = 5432

[connections.my_postgres_db.staging]
host = "staging.example.com"
username = "myuser"
password = "${PG_PASSWORD}"  # Uses environment variable

[connections.my_postgres_db.production]
host = "prod.example.com"
username = "myuser"
password = "${PG_PASSWORD_PROD}"
```

### General Configuration

The main configuration is in `config/config.toml`:

```toml
locale = "en_US"

[paths]
database = "database"
connections = "database/connections"

[defaults]
max_workers = 8
parallel = true
single_sheet = true
single_file = true
cache = true
column_name = "connection"
environment = "staging"
```

## Usage

### Command Line Interface (CLI)

Run a query across multiple connections:

```bash
uv run main.py -c connection1 connection2 -q "SELECT * FROM users WHERE created_at > '2023-01-01'" -s results.xlsx
# or (if using python directly)
python main.py -c connection1 connection2 -q "SELECT * FROM users WHERE created_at > '2023-01-01'" -s results.xlsx
```

Available options:

- `-c, --connections`: Specify which connections to use (default: all available)
- `-q, --query`: SQL query to execute (required)
- `-s, --save-path`: Path to save results
- `--environment`: Database environment to use (staging, production, replica; default: staging)
- `--commit`: Commit DML operations (default: false, will rollback)
- `--output-format`: Output format (xlsx, json, csv)
- `--single-sheet`: Export all results to a single sheet (default: true)
- `--single-file`: Export all connections to a single file (default: true)
- `--ignore-cache`: Ignore cached query results (default: false)

### Graphical User Interface (GUI)

Launch the GUI application:

```bash
uv run gui.py
# or (if using python directly)
python gui.py
```

The GUI provides:
- Connection management and filtering
- Query editor with syntax highlighting
- Results preview in a spreadsheet-like view
- Export options with formatting
- Caching controls

## Supported Databases

The tool currently supports:
- PostgreSQL
- MySQL
- Microsoft SQL Server
- SQLite
- Oracle

The architecture is designed to easily support additional databases by adding connection string formats in the `conn_formats` dictionary.

## Security

Passwords in connection files can be:
- Encrypted using the `encrypt_passwords.py` script
- Referenced from environment variables using `${ENV_VAR_NAME}` syntax

## Examples

### Simple query across all connections
```bash
uv run main.py -q "SELECT COUNT(*) FROM users" -s user_counts.json
# or (if using python directly)
python main.py -q "SELECT COUNT(*) FROM users" -s user_counts.json
```

### Query specific connections with different output format
```bash
uv run main.py -c db1 db2 db3 -q "SELECT * FROM orders WHERE date > '2023-01-01'" -s orders.xlsx --output-format xlsx
# or (if using python directly)
python main.py -c db1 db2 db3 -q "SELECT * FROM orders WHERE date > '2023-01-01'" -s orders.xlsx --output-format xlsx
```

### Execute DML operation with commit
```bash
uv run main.py -c db1 db2 -q "UPDATE users SET status = 'inactive' WHERE last_login < '2022-01-01'" --commit
# or (if using python directly)
python main.py -c db1 db2 -q "UPDATE users SET status = 'inactive' WHERE last_login < '2022-01-01'" --commit
```

## Architecture

The project follows a modular architecture:

- `db_tools/database/`: Database connection management and query execution
- `db_tools/gui/`: GUI components using CustomTkinter
- `db_tools/exporter.py`: Result export functionality
- `db_tools/security.py`: Password encryption/decryption

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]