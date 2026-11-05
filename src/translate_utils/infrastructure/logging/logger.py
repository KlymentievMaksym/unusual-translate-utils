import logging
import sys
from datetime import datetime

from translate_utils.infrastructure.filesystem.path import DEFAULT_DIR_FOR_LOGS, create_default_dirs
from translate_utils.infrastructure.logging.log_cleaner import cleanup_old_logs


def setup_logging(command_name: str) -> logging.Logger:
    create_default_dirs()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    cleanup_old_logs(DEFAULT_DIR_FOR_LOGS, max_files=10)

    curr_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            filename=DEFAULT_DIR_FOR_LOGS / f"{command_name}_{curr_time}.log", encoding="utf-8"
        ),
    ]

    logging.basicConfig(
        handlers=handlers,
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        force=True,
    )
    return logging.getLogger(command_name)


def get_logger(command_name: str | None = None) -> logging.Logger:
    return logging.getLogger(command_name)
