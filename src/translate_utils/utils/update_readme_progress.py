import re
from pathlib import Path

from translate_utils.utils.logger import get_logger
from translate_utils.utils.visualize.markdown import generate_progress_markdown

LOGGER = get_logger(__name__)
README_PATH = Path(__file__).parent.parent / "README.md"

def update_readme_progress(generated_table):
    if README_PATH.exists():
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r"(<!-- PROGRESS_START -->)(.*?)(<!-- PROGRESS_END -->)"
        replacement = f"\\1\n{generated_table}\n\\3"
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated_content)
        LOGGER.info("README.md translation status updated")
    else:
        LOGGER.error(f"README.md not found, {README_PATH.absolute()}")
