# Project TODO List

This document outlines the main areas for improvement in the `db_tools` project, based on a recent code review.

## 1. Critical: Add a Comprehensive Test Suite

**Problem:** The project currently has no automated tests. This makes it difficult to refactor code or add new features without risking regressions.

**Solution:**
-   Create a `tests/` directory.
-   **Unit Tests:** Add unit tests for individual functions. A good place to start would be testing utility functions and business logic. For example, `db_tools/database/runner.py`'s `_verify_query_type` function should be tested with various SQL queries to ensure it behaves as expected.
-   **Integration Tests:** Write tests that cover the entire workflow of the application. This would involve setting up a test database, running the `main.py` script with various arguments, and asserting that the output is correct.

## 2. Major: Remove Interactive Prompts from the CLI

**Problem:** The CLI contains interactive `input()` prompts in two places:
1.  `main.py` in `validate_args` when a directory doesn't exist.
2.  `db_tools/database/runner.py` in `execute_query_multi_db` when checking for cached results.

This is a major design flaw for a CLI tool as it prevents automation (e.g., in cron jobs or CI/CD pipelines).

**Solution:**
-   **Fail Fast:** Instead of prompting, the application should exit with a non-zero status code and print a clear error message to `stderr`.
-   **Use Flags for Control:** The caching mechanism should be controlled explicitly via command-line flags like `--use-cache` or `--force-recache`, not by an interactive prompt.

## 3. Bug: Fix Inflexible Export Logic

**Problem:** The `--output-format` argument is implemented, but the tool is hardcoded to always call `export_to_excel` in `main.py`. This is a bug and does not align with user expectations.

**Solution:**
-   Implement a dispatch mechanism in `main.py` to call the correct exporter based on the `args.output_format` value.

    ```python
    # Example in main()
    if args.output_format == "xlsx":
        export_to_excel(df, ...)
    elif args.output_format == "json":
        # export_to_json(df, ...) - Needs to be implemented
        df.to_json(args.save_path, orient='records')
    elif args.output_format == "csv":
        # export_to_csv(df, ...) - Needs to be implemented
        df.to_csv(args.save_path, index=False)
    ```

## 4. Refactor: Improve Query Type Detection

**Problem:** The `_verify_query_type` function is brittle and unreliable.
-   It has a bug where it analyzes the original query string instead of the comment-stripped `clean_query`.
-   It uses a naive substring search to detect DML statements within `WITH` clauses, which can lead to incorrect classifications.

**Solution:**
-   **Use a dedicated SQL parsing library like `sqlparse`.** This is the most robust solution. It will accurately parse the SQL and identify the statement type, regardless of comments, CTEs, or formatting.

    ```python
    import sqlparse

    def get_query_type(query: str) -> str:
        statement = sqlparse.parse(query)[0]
        return statement.get_type()

    # This would replace the logic in _verify_query_type
    ```

## 5. Refactor: Make Database Support Extensible

**Problem:** The `_build_connstring` function in `db_tools/database/manager.py` only supports PostgreSQL, and the logic is hardcoded in an `if/else` block.

**Solution:**
-   Refactor the function to use a dictionary-based approach to map database types to their connection string formats. This will make it much easier to add support for other databases like MySQL, SQLite, etc.

    ```python
    # Example of a more extensible approach
    def _build_connstring(self, config: Struct, environment: str) -> str:
        db_type = config.type
        
        conn_formats = {
            "postgresql": "postgresql+psycopg://{user}:{password}@{host}:{port}/{database}",
            "mysql": "mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
            # Add other database types here
        }

        if db_type not in conn_formats:
            raise NotImplementedError(f"Connection type '{db_type}' not implemented!")

        # ... logic to get user, password, host, etc. ...
        
        return conn_formats[db_type].format(...)
    ```

## 6. Refactor: Simplify Bloated Functions

**Problem:** Some functions are overly complex and handle too many responsibilities, making them hard to read and maintain.
-   `create_arguments` in `main.py` is very long.
-   `export_to_excel` in `db_tools/exporter.py` has complex logic for handling different export configurations.

**Solution:**
-   **`create_arguments`:** Consider grouping related arguments. For less frequently used options, consider moving them to the `.config/config.toml` file to simplify the CLI.
-   **`export_to_excel`:** Break this function down into smaller, more focused helper functions (e.g., `_export_single_file_single_sheet`, `_export_single_file_multi_sheet`, etc.) to reduce complexity.
