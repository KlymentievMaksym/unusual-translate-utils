import re
import argparse
from pathlib import Path

from utils.dataclasses import CleanupRepeatsArgs, CheckTranslationProgressArgs, DialogueLine

RE_LABEL = re.compile(r'^translate\s+\w+\s+(\w+):')
RE_STRINGS_BLOCK = re.compile(r'^translate\s+\w+\s+strings:')

RE_SCRIPT_POS = re.compile(r'^\s*#\s*(?:.*[/\\])?([^/\\]+\.rpy:\d+)')
RE_COMMENT_TEXT = re.compile(r'^\s*#\s*(?:(\w+)\s+)?\"(.*)\"$')
RE_ACTIVE_TEXT = re.compile(r'^\s*(?:(\w+)\s+)?\"(.*)\"$')

RE_OLD = re.compile(r'^\s*old\s+("""|")(.*)\1$', re.DOTALL)
RE_NEW = re.compile(r'^\s*new\s+("""|")(.*)\1$', re.DOTALL)

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
    return CheckTranslationProgressArgs.from_namespace(parser.parse_args())

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
        old_match = RE_OLD.match(line)
        if old_match:
            self.temp_old_string = old_match.group(2)
        else:
            new_match = RE_NEW.match(line)
            if new_match and self.temp_old_string is not None:
                self.ui_strings[self.temp_old_string] = new_match.group(2)
                self.temp_old_string = None



# def parse_rpy_translations(filepath: str):
#     """
#     Parses a Ren'Py translation file and efficiently stores dialogue and UI strings.
#     """
#     dialogues: dict[str, DialogueLine] = {} 
#     ui_strings: dict[str, str] = {}

#     current_mode = None
#     current_label = None
    
#     temp_script_pos = None
#     temp_character = None
#     temp_original_text = None
#     temp_old_string = None

#     with open(filepath, 'r', encoding='utf-8') as file:
#         for line in file:
#             line = line.strip('\n')
#             stripped_line = line.strip()

#             if not stripped_line:
#                 continue

#             pos_match = re_script_pos.match(line)
#             if pos_match:
#                 temp_script_pos = pos_match.group(1)
#                 continue

#             if re_strings_block.match(line):
#                 current_mode = 'strings'
#                 continue

#             label_match = re_label.match(line)
#             if label_match:
#                 current_mode = 'dialogue'
#                 current_label = label_match.group(1) 

#                 temp_character = None
#                 temp_original_text = None 
#                 continue

#             if current_mode == 'dialogue':
#                 if stripped_line.startswith('#'):
#                     comment_match = re_comment_text.match(line)
#                     if comment_match:
#                         temp_character = comment_match.group(1)
#                         temp_original_text = comment_match.group(2)
#                 elif not stripped_line.startswith('#') and temp_original_text is not None:
#                     active_match = re_active_text.match(line)
#                     if active_match:
#                         translated_text = active_match.group(2)
                        
#                         dialogues[current_label] = DialogueLine(
#                             script_pos=temp_script_pos,
#                             character=temp_character,
#                             original=temp_original_text,
#                             translated=translated_text
#                         )
#                         temp_original_text = None

#             elif current_mode == 'strings':
#                 old_match = re_old.match(line)
#                 if old_match:
#                     temp_old_string = old_match.group(1)
#                 else:
#                     new_match = re_new.match(line)
#                     if new_match and temp_old_string is not None:
#                         ui_strings[temp_old_string] = new_match.group(1)
#                         temp_old_string = None 

#     return dialogues, ui_strings

