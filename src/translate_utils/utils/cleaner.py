from pathlib import Path

from translate_utils.utils.dataclasses import DialogueLine
from translate_utils.utils.parser import RE_STRINGS_BLOCK, RE_OLD_SINGLE, RE_OLD_MULTI, RE_NEW_SINGLE, RE_NEW_MULTI


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
    skip_upcoming_new = False
    in_multi_old = False
    in_skip_multi_new = False

    old_buffer: list[str] = []
    old_indent = ""

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
                if in_multi_old:
                    old_buffer.append(line)
                    if '"""' in line:
                        in_multi_old = False

                        raw_block = "".join(old_buffer)
                        text = raw_block.split('"""', 2)[1].strip()

                        if text in text_to_pos:
                            skip_upcoming_new = True
                            script_pos = ", ".join(text_to_pos[text])
                            output_lines.append(f"{old_indent}# {script_pos}\n")
                            replaced_count += 1
                        else:
                            output_lines.extend(old_buffer)

                        old_buffer.clear()
                    continue

                if in_skip_multi_new:
                    if '"""' in line:
                        in_skip_multi_new = False
                    continue

                old_multi_match = RE_OLD_MULTI.match(line)
                if old_multi_match:
                    in_multi_old = True
                    old_indent = old_multi_match.group(1)
                    old_buffer.append(line)

                    if line.count('"""') >= 2:
                        in_multi_old = False
                        text = line.split('"""', 2)[1].strip()
                        if text in text_to_pos:
                            skip_upcoming_new = True
                            script_pos = ", ".join(text_to_pos[text])
                            output_lines.append(f"{old_indent}# {script_pos}\n")
                            replaced_count += 1
                        else:
                            output_lines.extend(old_buffer)
                        old_buffer.clear()
                    continue

                old_single_match = RE_OLD_SINGLE.match(line)
                if old_single_match:
                    indent = old_single_match.group(1)
                    text = old_single_match.group(2)
                    
                    if text in text_to_pos:
                        skip_upcoming_new = True
                        script_pos = ", ".join(text_to_pos[text])
                        output_lines.append(f"{indent}# {script_pos}\n")
                        replaced_count += 1
                        continue

                if skip_upcoming_new:
                    if RE_NEW_MULTI.match(line):
                        skip_upcoming_new = False
                        if line.count('"""') < 2:
                            in_skip_multi_new = True
                        continue
                        
                    elif RE_NEW_SINGLE.match(line):
                        skip_upcoming_new = False
                        continue

            output_lines.append(line)

    return output_lines, replaced_count