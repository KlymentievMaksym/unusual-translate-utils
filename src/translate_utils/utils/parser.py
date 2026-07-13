import re
import argparse
from pathlib import Path

from translate_utils.utils.dataclasses import CleanupRepeatsArgs, CheckTranslationProgressArgs, DialogueLine, Progress

RE_LABEL = re.compile(r'^translate\s+\w+\s+(\w+):')
RE_STRINGS_BLOCK = re.compile(r'^translate\s+\w+\s+strings:')

RE_SCRIPT_POS = re.compile(r'^\s*#\s*(?:.*[/\\])?([^/\\]+\.rpy:\d+)')
RE_COMMENT_TEXT = re.compile(r'^\s*#\s*(?:(\w+)\s+)?\"(.*)\"$')
RE_ACTIVE_TEXT = re.compile(r'^\s*(?:(\w+)\s+)?\"(.*)\"$')

# RE_OLD = re.compile(r'^(\s*)old\s+("""|")(.*)\2$', re.DOTALL)
# RE_NEW = re.compile(r'^\s*new\s+("""|")(.*)\1$', re.DOTALL)
RE_OLD_SINGLE = re.compile(r'^(\s*)old\s+\"(.*)\"$')
RE_NEW_SINGLE = re.compile(r'^\s*new\s+\"(.*)\"$')

RE_OLD_MULTI = re.compile(r'^(\s)*old\s+\"\"\"')
RE_NEW_MULTI = re.compile(r'^\s*new\s+\"\"\"')

def cleanup_repeats_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepaths", 
        type=str, 
        nargs="+",
        help="Relative or Absolute Path to the .rpy translation file"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Save with new name"
    )
    return CleanupRepeatsArgs.from_namespace(parser.parse_args())

def check_translation_progress_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepaths", 
        type=str, 
        nargs="*",
        help="Relative or Absolute Path to the .rpy translation file or directory of them"
    )
    parser.add_argument(
        "--update-readme",
        type=str, 
        default=None,
        help="Update README"
    )
    return CheckTranslationProgressArgs.from_namespace(parser.parse_args())

def calculate_file_progress(filepath: Path, parser: RpyTranslationParser) -> tuple[int, int, Progress, Progress]:
    """
    Parses a single file and returns (translated_count, total_count).
    """
    dialogues, ui_strings = parser.parse_all(filepath)
    dialog_length = len(dialogues)
    string_length = len(ui_strings)

    total = dialog_length + string_length

    dialog_translated = 0
    string_translated = 0
    for label, dialog in dialogues.items():
        if dialog.original != dialog.translated and not dialog.translated.isascii():
            dialog_translated += 1
    for old, new in ui_strings.items():
        if old != new and not new.isascii():
            string_translated += 1

    translated = dialog_translated + string_translated

    return translated, total, Progress(dialog_translated, dialog_length), Progress(string_translated, string_length)

def get_raw_translation_data(paths_to_check: list[Path]):
    """Збирає дані без прив'язки до argparse та принтів."""
    parser = RpyTranslationParser()
    file_stats: dict[str, tuple[int, int]] = {}
    global_translated = 0
    global_total = 0
    dialog_progresses: list[Progress] = []
    string_progresses: list[Progress] = []
    
    rpy_files = []
    for target_path in paths_to_check:
        if target_path.is_file() and target_path.suffix == ".rpy":
            rpy_files.append(target_path)
        elif target_path.is_dir():
            rpy_files.extend(target_path.rglob("*.rpy"))
            
    rpy_files.sort(key=lambda path: path.name)

    for filepath in rpy_files:
        translated, total, dialog_progress, string_progress = calculate_file_progress(filepath, parser)
        if total > 0:
            dialog_progresses.append(dialog_progress)
            string_progresses.append(string_progress)
            file_stats[filepath.name] = (translated, total)
            global_translated += translated
            global_total += total
            
    return file_stats, global_translated, global_total, dialog_progresses, string_progresses

class RpyTranslationParser:
    """Handles the stateful parsing of Ren'Py translation files."""
    def __init__(self):
        self.dialogues: dict[str, DialogueLine] = {}
        self.ui_strings: dict[str, str] = {}

        self.current_mode = None
        self.current_label = None
        self.temp_script_pos = None
        self.temp_character = None
        self.temp_original_text = None
        self.temp_old_string = None
        
        self.in_multi_old = False
        self.in_multi_new = False
        self.multi_buffer: list[str] = []

    def _reset_state(self):
        """Clears stored data and state variables for a fresh parse."""
        self.dialogues.clear()
        self.ui_strings.clear()
        self.current_mode = None
        self.current_label = None
        self.temp_script_pos = None
        self.temp_character = None
        self.temp_original_text = None
        self.temp_old_string = None

        self.in_multi_old = False
        self.in_multi_new = False
        self.multi_buffer.clear()

    # ==========================================
    # Public Methods
    # ==========================================

    def parse_all(self, filepath: str | Path) -> tuple[dict[str, DialogueLine], dict[str, str]]:
        """Parses and returns both dialogues and UI strings."""
        self._run_parser(filepath, parse_dialogues=True, parse_strings=True)
        return self.dialogues, self.ui_strings

    def parse_dialogues_only(self, filepath: str | Path) -> dict[str, DialogueLine]:
        """Parses and returns ONLY dialogue lines."""
        self._run_parser(filepath, parse_dialogues=True, parse_strings=False)
        return self.dialogues

    def parse_strings_only(self, filepath: str | Path) -> dict[str, str]:
        """Parses and returns ONLY UI strings."""
        self._run_parser(filepath, parse_dialogues=False, parse_strings=True)
        return self.ui_strings

    # ==========================================
    # Internal Logic
    # ==========================================

    def _run_parser(self, filepath: str | Path, parse_dialogues: bool, parse_strings: bool):
        """Core file I/O loop. Uses flags to determine what to extract."""
        self._reset_state()
        with open(filepath, 'r', encoding='utf-8-sig') as file:
            for line in file:
                self._process_line(line, parse_dialogues, parse_strings)

    def _process_line(self, line: str, parse_dialogues: bool, parse_strings: bool):
        """Line orchestration. Normalizes the line and routes it if flags allow."""
        line = line.strip('\n')
        stripped_line = line.strip()

        if not stripped_line:
            return

        if self._check_state_transitions(line):
            return

        if self.current_mode == 'dialogue' and parse_dialogues:
            self._parse_dialogue(line, stripped_line)
        elif self.current_mode == 'strings' and parse_strings:
            self._parse_string(line)

    def _check_state_transitions(self, line: str) -> bool:
        """State Management. Updates modes and resets temp variables."""
        if self.in_multi_old or self.in_multi_new:
            return False

        pos_match = RE_SCRIPT_POS.match(line)
        if pos_match:
            self.temp_script_pos = pos_match.group(1)
            return True

        if RE_STRINGS_BLOCK.match(line):
            self.current_mode = 'strings'
            return True

        label_match = RE_LABEL.match(line)
        if label_match:
            self.current_mode = 'dialogue'
            self.current_label = label_match.group(1)

            self.temp_character = None
            self.temp_original_text = None
            return True
            
        return False

    def _parse_dialogue(self, line: str, stripped_line: str):
        """Dialogue Logic. Extracts and stores DialogueLines."""
        if stripped_line.startswith('#'):
            comment_match = RE_COMMENT_TEXT.match(line)
            if comment_match:
                self.temp_character = comment_match.group(1)
                self.temp_original_text = comment_match.group(2)
        elif self.temp_original_text is not None:
            active_match = RE_ACTIVE_TEXT.match(line)
            if active_match:
                self.dialogues[self.current_label] = DialogueLine(  # type: ignore
                    script_pos=self.temp_script_pos,
                    character=self.temp_character,
                    original=self.temp_original_text,
                    translated=active_match.group(2)
                )
                self.temp_original_text = None

    def _parse_string(self, line: str):
        """UI String Logic. Extracts and stores UI translations."""
        if self.in_multi_old:
            self.multi_buffer.append(line)
            if '"""' in line:
                self.in_multi_old = False
                self.temp_old_string = "\n".join(self.multi_buffer).replace('"""', '').strip()
                self.multi_buffer.clear()
            return
        
        if self.in_multi_new:
            self.multi_buffer.append(line)
            if '"""' in line:
                self.in_multi_new = False
                translated_text = "\n".join(self.multi_buffer).replace('"""', '').strip()
                
                if self.temp_old_string is not None:
                    self.ui_strings[self.temp_old_string] = translated_text
                    self.temp_old_string = None
                self.multi_buffer.clear()
            return

        if RE_OLD_MULTI.match(line):
            self.in_multi_old = True
            content = line.split('"""', 1)[1]
            if content:
                self.multi_buffer.append(content)
            return
        
        if RE_NEW_MULTI.match(line):
            self.in_multi_new = True
            content = line.split('"""', 1)[1]
            if content:
                self.multi_buffer.append(content)
            return
        
        old_match = RE_OLD_SINGLE.match(line)
        if old_match:
            self.temp_old_string = old_match.group(2)
        else:
            new_match = RE_NEW_SINGLE.match(line)
            if new_match and self.temp_old_string is not None:
                self.ui_strings[self.temp_old_string] = new_match.group(1)
                self.temp_old_string = None
