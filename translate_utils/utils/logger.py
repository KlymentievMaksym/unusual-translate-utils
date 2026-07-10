import sys
import logging
from pathlib import Path
from datetime import datetime

from utils.cleaner import cleanup_old_logs


sys.stdout.reconfigure(encoding='utf-8')

logs_dirname = Path(__file__).parent.parent / "logs" 
logs_dirname.mkdir(exist_ok=True)

def setup_logging(command_name: str) -> logging.Logger:
    cleanup_old_logs(logs_dirname, max_files=10)

    curr_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(filename=logs_dirname / f"{command_name}_{curr_time}.log", encoding="utf-8")
    ]

    logging.basicConfig(handlers=handlers, level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s', force=True)
    return logging.getLogger(command_name)

def get_logger(command_name: str | None = None) -> logging.Logger:
    return logging.getLogger(command_name)