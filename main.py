import argparse
from pathlib import Path

from db_tools.database import DBConnectionRunner
from db_tools.exporter import export_data
from db_tools.extras import get_available_connections
from db_tools.logger import get_logger, setup_logging

connections = get_available_connections()


def create_arguments() -> argparse.ArgumentParser:
    """
    Creates and configures the argument parser for the command-line interface.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="Database Query Executor",
        description="Conecta em diversas bases de dados e executa queries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--connections",
        type=str,
        required=False,
        nargs="+",
        choices=connections,
        help="Utilizar somente estas conexões. Conexões disponíveis na configuração 'connections'.",
    )
    parser.add_argument("-q", "--query", type=str, required=True)
    parser.add_argument(
        "-s",
        "--save-path",
        type=str,
    )
    parser.add_argument(
        "--environment",
        type=str,
        default="staging",
        choices=["staging", "production", "replica"],
    )
    parser.add_argument(
        "--commit", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument("--output-format", type=str, choices=["xlsx", "json", "csv"])
    parser.add_argument(
        "--single-sheet", action=argparse.BooleanOptionalAction, default=True
    )
    parser.add_argument(
        "--single-file", action=argparse.BooleanOptionalAction, default=True
    )
    parser.add_argument(
        "--ignore-cache", action=argparse.BooleanOptionalAction, default=False
    )

    return parser


def main():
    """
    The main function of the application.
    """
    parser = create_arguments()
    args = parser.parse_args()
    runner = DBConnectionRunner(
        args.environment,
        args.connections,
        args.save_path,
    )
    if args.output_format is not None:
        output_format = args.output_format
    else:
        if args.save_path is not None:
            output_format = Path(args.save_path).suffix[1:]
    try:
        df = runner.execute_query_multi_db(
            args.query,
            args.commit,
            args.ignore_cache,
        )
        if args.save_path:
            export_data(
                args.save_path,
                df,
                output_format,
                args.single_file,
                args.single_sheet,
                runner.configurations.column_name,
            )
    finally:
        runner.close_all()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    setup_logging()
    logger = get_logger("db_tools")

    main()
