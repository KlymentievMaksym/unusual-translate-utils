import re
from pathlib import Path

from translate_utils.utils.logger import get_logger
from translate_utils.utils.visualize.markdown import generate_progress_markdown

LOGGER = get_logger(__name__)

def update_readme_progress(generated_table, readme_path):
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
