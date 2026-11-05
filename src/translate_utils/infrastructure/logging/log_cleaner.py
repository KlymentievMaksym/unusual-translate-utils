from pathlib import Path


def cleanup_old_logs(log_dir: Path, logs_name: str = "", max_files: int = 10) -> None:
    logs = sorted(log_dir.glob(logs_name + "*.log"), key=lambda x: x.stat().st_mtime)

    while len(logs) >= max_files:
        oldest_log = logs.pop(0)
        oldest_log.unlink()
