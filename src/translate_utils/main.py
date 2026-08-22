import argparse
import sys

from translate_utils.presentation.runners import Command


def main() -> None:
    parser = argparse.ArgumentParser(prog="gwt", description="GW-Translate command line interface.")

    subparsers = parser.add_subparsers(
        dest="command",
        title="Available commands",
        help=(
            "Run 'gwt <command> --help' for more info. "
            "If no command is provided, the app will launch."
        ),
    )

    for cmd in Command:
        if cmd == Command.DEFAULT:
            continue

        subparsers.add_parser(cmd.cli_name, help=cmd.description, add_help=False)

    args, unknown_args = parser.parse_known_args()

    if args.command is None:
        if unknown_args:
            parser.print_help()
            sys.exit(1)

        Command.DEFAULT.execute()
    else:
        sys.argv = [sys.argv[0]] + unknown_args

        selected_cmd = Command.from_cli_name(args.command)
        selected_cmd.execute()


if __name__ == "__main__":  # pragma: no cover
    main()
