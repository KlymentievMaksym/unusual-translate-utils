import re
from pathlib import Path

from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

def update_readme_progress(generated_table, readme_path: str | Path):
    readme_path = Path(readme_path)
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r"(<!-- PROGRESS_START -->)(.*?)(<!-- PROGRESS_END -->)"
        replacement = f"\\1\n{generated_table}\n\\3"
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        LOGGER.info("README.md translation status updated")
    else:
        LOGGER.error(f"README.md not found, {readme_path.absolute()}")
