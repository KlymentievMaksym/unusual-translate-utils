import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from translate_utils.core.cleaner import TranslationCleaner
from translate_utils.core.interfaces import CleanStrategy
from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanMethod
from translate_utils.infrastructure.cache import CachedFileReader
from translate_utils.infrastructure.io import read_renpy_file, write_renpy_file
from translate_utils.infrastructure.parser import RegexDialogueParser
from translate_utils.infrastructure.parsers.extractors import strings_block_extractor
from translate_utils.infrastructure.parsers.regexes import RE_STRINGS_CONFIG, RE_TRANSLATE_CONFIG
from translate_utils.services.cleanup_service import CleanupService
from translate_utils.services.mappers import build_reverse_lookup


class CleanTab(Static):
    cleaned_file_path: str = ""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="clean_container"):
            yield Label("Select Target File:", classes="section_title")
            with Horizontal(classes="input_row"):
                yield Button("Browse...", id="btn_browse", variant="primary")
                yield Input(placeholder="Path to .rpy file...", id="input_target_file")

            yield Label("Cleaning Method:", classes="section_title")
            yield Select(
                options=[
                    ("Just add comment", "add_comment"),
                    ("Keep only comment ", "only_comment"),
                    ("Remove fully with no comment", "empty"),
                ],
                value="only_comment",
                id="select_method",
            )
            yield Label("Output Settings:", classes="section_title")
            yield Checkbox("Overwrite original file", value=True, id="chk_overwrite")

            with Horizontal(classes="input_row"):
                yield Input(placeholder="Output Directory", id="input_out_dir", disabled=True)

            with Horizontal(classes="input_row"):
                yield Input(placeholder="New File Name", id="input_out_name", disabled=True)

            with Horizontal(classes="action_row"):
                yield Button("Clean File", id="btn_run_clean", variant="error")
                yield Button("Open in VS Code", id="btn_vscode", variant="success", disabled=True)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "chk_overwrite":
            is_overwriting = event.value
            self.query_one("#input_out_dir", Input).disabled = is_overwriting
            self.query_one("#input_out_name", Input).disabled = is_overwriting

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_browse":
            self.open_file_explorer()
        elif event.button.id == "btn_run_clean":
            self.prepare_and_run_cleaning()
        elif event.button.id == "btn_vscode" and self.cleaned_file_path:
            subprocess.Popen(["code.cmd", self.cleaned_file_path])
            self.notify(f"Opened {Path(self.cleaned_file_path).name} in VS Code!")

    @work(thread=True)
    def open_file_explorer(self) -> None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.askopenfilename(
            title="Select Translation File",
            filetypes=[("Ren'Py Files", "*.rpy"), ("All Files", "*.*")],
        )
        root.destroy()
        if file_path:

            def update_input() -> None:
                self.query_one("#input_target_file", Input).value = file_path

            self.app.call_from_thread(update_input)

    def prepare_and_run_cleaning(self) -> None:
        target_file = self.query_one("#input_target_file", Input).value
        method = self.query_one("#select_method", Select).value
        overwrite = self.query_one("#chk_overwrite", Checkbox).value
        out_dir = self.query_one("#input_out_dir", Input).value
        out_name = self.query_one("#input_out_name", Input).value

        if not target_file or not Path(target_file).exists():
            self.notify("Please select a valid file first!", severity="error")
            return

        original_path = Path(target_file)

        if overwrite:
            final_output_path = original_path
        else:
            save_dir = Path(out_dir) if out_dir else original_path.parent
            save_name = out_name or f"{original_path.stem}_cleaned{original_path.suffix}"
            final_output_path = save_dir / save_name

        self.query_one("#btn_run_clean", Button).disabled = True

        self._execute_cleaning_task(original_path, final_output_path, method)

    @work(thread=True)
    def _execute_cleaning_task(
        self, target_path: Path, output_path: Path, method: CleanMethod
    ) -> None:
        try:
            file_reader = CachedFileReader(read_renpy_file)
            file_parser = RegexDialogueParser(RE_TRANSLATE_CONFIG)
            file_cleaner = TranslationCleaner(RE_STRINGS_CONFIG.pattern, strings_block_extractor)
            mapper = build_reverse_lookup
            cleanup_service = CleanupService(
                file_reader=file_reader,
                file_parser=file_parser,
                file_cleaner=file_cleaner,
                file_writer=write_renpy_file,
                mapper=mapper,
            )

            clean_method: CleanStrategy = AVAILABLE_METHODS.get(
                method, AVAILABLE_METHODS[CleanMethod.ONLY_COMMENT]
            )
            clean_results = cleanup_service.clean_and_save(
                filepath=target_path, clean_method=clean_method, new_name=output_path
            )

            def update_ui_success() -> None:
                self.query_one("#btn_run_clean", Button).disabled = False
                self.query_one("#btn_vscode", Button).disabled = False
                self.notify(
                    f"Success! Replaced {clean_results.replaced_count} duplicates.\n"
                    f"Saved to: {output_path.name}",
                    title="Cleaned",
                    timeout=5,
                )

            self.app.call_from_thread(update_ui_success)
        except Exception as e:

            def update_ui_error(e: Exception) -> None:
                self.query_one("#btn_run_clean", Button).disabled = False
                self.notify(f"Error processing file:\n{str(e)}", severity="error", timeout=10)

            self.app.call_from_thread(update_ui_error, e)
