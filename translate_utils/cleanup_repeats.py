import argparse
import re
from dataclasses import dataclass

@dataclass(slots=True)
class DialogueLine:
    script_pos: str | None
    character: str | None
    original: str
    translated: str

def parse_rpy_translations(filepath: str):
    """
    Parses a Ren'Py translation file and efficiently stores dialogue and UI strings.
    """
    dialogues: dict[str, DialogueLine] = {} 
    ui_strings: dict[str, str] = {}

    re_label = re.compile(r'^translate\s+\w+\s+(\w+):?')
    re_strings_block = re.compile(r'^translate\s+\w+\s+strings:')
    re_script_pos = re.compile(r'^\s*#\s*(?:.*[/\\])?([^/\\]+\.rpy:\d+)')
    re_comment_text = re.compile(r'^\s*#\s*(?:(\w+)\s+)?\"(.*)\"$')
    re_active_text = re.compile(r'^\s*(?:(\w+)\s+)?\"(.*)\"$')
    re_old = re.compile(r'^\s*old\s+\"(.*)\"$')
    re_new = re.compile(r'^\s*new\s+\"(.*)\"$')

    current_mode = None
    current_label = None
    
    temp_script_pos = None
    temp_character = None
    temp_original_text = None
    temp_old_string = None

    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip('\n')
            stripped_line = line.strip()

            if not stripped_line:
                continue

            pos_match = re_script_pos.match(line)
            if pos_match:
                temp_script_pos = pos_match.group(1)
                continue

            if re_strings_block.match(line):
                current_mode = 'strings'
                continue

            label_match = re_label.match(line)
            if label_match:
                current_mode = 'dialogue'
                current_label = label_match.group(1) 

                temp_character = None
                temp_original_text = None 
                continue

            if current_mode == 'dialogue':
                if stripped_line.startswith('#'):
                    comment_match = re_comment_text.match(line)
                    if comment_match:
                        temp_character = comment_match.group(1)
                        temp_original_text = comment_match.group(2)
                elif not stripped_line.startswith('#') and temp_original_text is not None:
                    active_match = re_active_text.match(line)
                    if active_match:
                        translated_text = active_match.group(2)
                        
                        dialogues[current_label] = DialogueLine(
                            script_pos=temp_script_pos,
                            character=temp_character,
                            original=temp_original_text,
                            translated=translated_text
                        )
                        temp_original_text = None

            elif current_mode == 'strings':
                old_match = re_old.match(line)
                if old_match:
                    temp_old_string = old_match.group(1)
                else:
                    new_match = re_new.match(line)
                    if new_match and temp_old_string is not None:
                        ui_strings[temp_old_string] = new_match.group(1)
                        temp_old_string = None 

    return dialogues, ui_strings

def write_cleaned_file(filepath: str, dialogues: dict[str, DialogueLine], is_same_name: bool):
    """
    Reads the original file, replaces duplicate strings with their script_pos comment, 
    and writes to a new '_cleaned.rpy' file.
    """
    # reverse lookup: Map "Original Text" -> "script.rpy:150"
    text_to_pos: dict[str, list[str]] = {}
    for data in dialogues.values():
        if data.original and data.script_pos:
            if data.original not in text_to_pos:
                text_to_pos[data.original] = []
            
            text_to_pos[data.original].append(data.script_pos)

    re_strings_block = re.compile(r'^translate\s+\w+\s+strings:')
    re_label = re.compile(r'^translate\s+\w+\s+(\w+):?')

    re_old = re.compile(r'^(\s*)old\s+\"(.*)\"$')
    re_new = re.compile(r'^\s*new\s+\".*\"$')

    output_lines = []
    current_mode = None
    skip_next_new = False
    replaced_count = 0

    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            stripped_line = line.strip()

            if re_strings_block.match(stripped_line):
                current_mode = 'strings'
                output_lines.append(line)
                continue

            if re_label.match(stripped_line):
                current_mode = 'dialogue'
                output_lines.append(line)
                continue

            if current_mode == 'strings':
                old_match = re_old.match(line)
                if old_match:
                    indent = old_match.group(1)  # e.g., "    "
                    text = old_match.group(2)    # e.g., "If you don't wake up..."
                    if text in text_to_pos:
                        script_pos = ", ".join(text_to_pos[text])
                        output_lines.append(f"{indent}# {script_pos}\n")
                        output_lines.append(line)
                        replaced_count += 1
                        continue

            output_lines.append(line)

    if not is_same_name:
        out_filepath = filepath.replace('.rpy', '_cleaned.rpy')
    with open(out_filepath, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    print(f"\n--- Cleanup Complete ---")
    print(f"Replaced {replaced_count} duplicate strings.")
    print(f"Saved cleaned file to: {out_filepath}")

def parse_args():
    parser = argparse.ArgumentParser(description="Parse Ren'Py translation files (.rpy) efficiently.")
    parser.add_argument(
        "--filepath", 
        type=str, 
        help="Relative or Absolute Path to the .rpy translation file (e.g., ukrainian.rpy)"
    )
    parser.add_argument(
        "--same-name", 
        action="store_true", 
        help="Save with same name"
    )
    return parser.parse_args()

def cleanup_repeats():
    args = parse_args()

    print(f"Loading and parsing: {args.filepath}...")
    dialogues, menu_strings = parse_rpy_translations(args.filepath)

    print(f"Lengths: scripts {len(dialogues)}, strings {len(menu_strings)}")
    
    # print("\n--- Example Dialogue Output ---")
    # if "start_c16ed4c8" in dialogues:
    #     line_data = dialogues["start_c16ed4c8"]
    #     print(f"Script_pos: {line_data.script_pos}")
    #     print(f"Character : {line_data.character}")
    #     print(f"Original  : {line_data.original}")
    #     print(f"Translated: {line_data.translated}")

    # print("\n--- Example UI Strings Output ---")
    # target_string = "{sc=2}{outlinecolor=#000000}{i}But this time it is special!"
    # if target_string in menu_strings:
    #     print(f"Original: {target_string}")
    #     print(f"New     : {menu_strings[target_string]}")

    write_cleaned_file(args.filepath, dialogues=dialogues, is_same_name=args.same_name)

if __name__ == "__main__":
    cleanup_repeats()