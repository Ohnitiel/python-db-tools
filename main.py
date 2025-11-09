import argparse
from pathlib import Path

import openpyxl

from lib.extras import find_root_dir
from runner import DBConnectionRunner

config_path = Path(find_root_dir(["pyproject.toml"]))


def create_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Database Query Executor",
        description="Conecta em diversas bases de dados e executa queries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c", "--connections", type=str, required=False, nargs="+", choices=[]
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
        default="homologacao",
        choices=["homologacao", "producao", "replica"],
    )
    parser.add_argument("--commit", type=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--no-parallel", type=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument("--output-format", type=str, choices=["xlsx", "json", "csv"])
    parser.add_argument(
        "--format-excel", type=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "--separate-sheets", type=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "--separate-files", type=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument("--column-name", type=str)
    parser.add_argument("-j", "--max-workers", type=int)

    return parser


def validate_args(args: argparse.Namespace):
    if args.separate_sheets and args.separate_files:
        # TODO Add a picker/raise error/prioritize one?
        pass

    if args.save_path is not None:
        args.save_path = Path(args.save_path)
        if not args.save_path.parent.exists():
            print("Diretório informado não existe!")
            response = input("Deseja criá-lo?")
            if response.lower() == "s":
                args.save_path.parent.mkdirs(exist_ok=True, parents=True)


def format_excel_file(file_path: Path):
    wb = openpyxl.load_workbook(file_path)


def main():
    parser = create_arguments()
    args = parser.parse_args()
    validate_args(args)
    runner = DBConnectionRunner(
        args.connections,
        args.max_workers,
        args.save_path,
        args.output_format,
    )
    add_connection_column = True if args.column_name else False
    df = runner.execute_query_multi_db(
        args.query,
        args.commit,
        args.no_parallel,
        add_connection_column,
        args.column_name,
    )


if __name__ == "__main__":
    main()
