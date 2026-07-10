from pathlib import Path

from utils.dataclasses import DialogueLine
from utils.parser import RE_STRINGS_BLOCK, RE_OLD, RE_NEW


def cleanup_old_logs(log_dir: Path, logs_name: str = "", max_files: int = 10):
    logs = sorted(log_dir.glob(logs_name + "*.log"), key=lambda x: x.stat().st_mtime)

    while len(logs) >= max_files:
        oldest_log = logs.pop(0)
        oldest_log.unlink()

def process_cleaned_lines(filepath: str | Path, dialogues: dict[str, DialogueLine]) -> tuple[list[str], int]:
    """
    Reads the original file, replaces duplicate strings with their script_pos comment.
    Returns the new list of lines and the count of replacements.
    """
    # Reverse lookup: Map "Original Text" -> ["script.rpy:150", "script.rpy:180"]
    text_to_pos: dict[str, list[str]] = {}
    for data in dialogues.values():
        if data.original and data.script_pos:
            if data.original not in text_to_pos:
                text_to_pos[data.original] = []
            text_to_pos[data.original].append(data.script_pos)

    current_mode = None
    do_skip_next = False

    output_lines = []
    replaced_count = 0

    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            stripped_line = line.strip()

            if RE_STRINGS_BLOCK.match(stripped_line):
                current_mode = 'strings'
                output_lines.append(line)
                continue

            if current_mode == 'strings':
                if do_skip_next:
                    # output_lines.append(line)
                    do_skip_next = False
                    continue

                old_match = RE_OLD.match(line)
                if old_match:
                    indent = old_match.group(1)  # e.g., "    "
                    text = old_match.group(3)    # e.g., "If you don't wake up..."
                    
                    if text in text_to_pos:
                        do_skip_next = True
                        script_pos = ", ".join(text_to_pos[text])
                        output_lines.append(f"{indent}# {script_pos}\n")
                        # output_lines.append(line)
                        replaced_count += 1
                        continue

            output_lines.append(line)

    return output_lines, replaced_count