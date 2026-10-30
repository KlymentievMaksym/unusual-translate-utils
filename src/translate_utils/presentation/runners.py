from enum import Enum

from translate_utils.core.interfaces import CommandStrategy


def run_app() -> None:
    """
    Initializes and runs the Textual User Interface.
    """
    from translate_utils.presentation.ui.app import GWTranslateApp

    app = GWTranslateApp()
    app.run()


def run_clean() -> None:
    """Executes the cleanup script."""
    from translate_utils.presentation.cli.cleanup_repeats import cleanup_repeats

    cleanup_repeats()


def run_compare() -> None:
    """Executes the compare script."""
    from translate_utils.presentation.cli.compare_dirs import compare_dirs

    compare_dirs()


def run_status() -> None:
    """Executes the translation progress check script."""
    from translate_utils.presentation.cli.check_progress import check_translation_progress

    check_translation_progress()


def run_check() -> None:
    """Executes the translation language check script."""
    from translate_utils.presentation.cli.check_language import check_language

    check_language()


class Command(Enum):
    """
    Rich Enum implementing the Strategy pattern.
    Each member holds its CLI string representation and the execution strategy.
    """

    APP = ("app", run_app, "Run an app")
    CLEAN = ("clean", run_clean, "Run clean from repeats for file, files or directory")
    COMPARE = ("compare", run_compare, "Run compare for directories")
    STATUS = ("status", run_status, "Run status of translation for file, files or directory")
    CHECK = ("check", run_check, "Run language check of translation for file, files or directory")
    DEFAULT = APP

    def __init__(self, cli_name: str, strategy: CommandStrategy, description: str) -> None:
        self.cli_name = cli_name
        self.strategy = strategy
        self.description = description

    def execute(self) -> None:
        """Executes the command strategy attached to the enum member."""
        self.strategy()

    @classmethod
    def from_cli_name(cls, cli_name: str) -> "Command":
        """Factory method to get the Command by its CLI string."""
        for command in cls:
            if command.cli_name == cli_name:
                return command
        raise ValueError(f"Unknown command name: {cli_name}")
