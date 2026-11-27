import io
import logging
import sys
from datetime import datetime
from pathlib import Path

from translate_utils.infrastructure.logging.log_cleaner import cleanup_old_logs


def setup_logging(command_name: str, logs_dir: Path, max_files: int = 10) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    cleanup_old_logs(logs_dir, max_files=max_files)

    curr_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_file = logs_dir / f"{command_name}_{curr_time}.log"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(filename=log_file, encoding="utf-8"),
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
