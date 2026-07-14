from pathlib import Path


DEFAULT_DIR_FOR_TRANSLATION = Path(__file__).parents[3] / "game" / "tl" / "ukrainian"
DEFAULT_DIR_FOR_TRANSLATION.mkdir(exist_ok=True)

DEFAULT_DIR_FOR_LOGS = Path(__file__).parents[3] / "logs" 
DEFAULT_DIR_FOR_LOGS.mkdir(exist_ok=True)