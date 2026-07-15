import os
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, Button, Input, Select, Checkbox
from textual.containers import VerticalScroll, Horizontal

from translate_utils.infrastructure.parser import RpyTranslationParser
from translate_utils.core.cleaner import TranslationCleaner
from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanStrategy
# from translate_utils.utils.saver import save_lines_to_file # (Ми напишемо збереження напряму, щоб підтримувати зміну директорії)

class CleanTab(Static):
    cleaned_file_path: str = ""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="clean_container"):
            # 1. Вибір файлу
            yield Label("1. Select Target File:", classes="section_title")
            with Horizontal(classes="input_row"):
                yield Button("Browse...", id="btn_browse", variant="primary")
                yield Input(placeholder="Path to .rpy file...", id="input_target_file")

            # 2. Метод очистки
            yield Label("2. Cleaning Method:", classes="section_title")
            yield Select(
                options=[
                    ("Remove exact duplicates", "exact"),
                    ("Remove empty translations", "empty"),
                    ("Keep latest only", "latest")
                ],
                value="exact",
                id="select_method"
            )

            # 3. Налаштування збереження
            yield Label("3. Output Settings:", classes="section_title")
            yield Checkbox("Overwrite original file", value=True, id="chk_overwrite")
            
            with Horizontal(classes="input_row"):
                yield Input(placeholder="Output Directory (leave empty for same folder)", id="input_out_dir", disabled=True)
            with Horizontal(classes="input_row"):
                yield Input(placeholder="New File Name (e.g. script_cleaned.rpy)", id="input_out_name", disabled=True)

            # 4. Дії
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
        elif event.button.id == "btn_vscode":
            if self.cleaned_file_path:
                subprocess.Popen(["code.cmd", self.cleaned_file_path])
                self.notify(f"Opened {Path(self.cleaned_file_path).name} in VS Code!")

    @work(thread=True)
    def open_file_explorer(self) -> None:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title="Select Translation File",
            filetypes=[("Ren'Py Files", "*.rpy"), ("All Files", "*.*")]
        )
        root.destroy()
        if file_path:
            def update_input():
                self.query_one("#input_target_file", Input).value = file_path
            self.app.call_from_thread(update_input)

    # --- НОВА ЛОГІКА ЗБОРУ ДАНИХ ТА ЗАПУСКУ БЕКЕНДУ ---
    
    def prepare_and_run_cleaning(self) -> None:
        """Збирає дані з UI у головному потоці та передає їх у фоновий воркер."""
        target_file = self.query_one("#input_target_file", Input).value
        method = self.query_one("#select_method", Select).value
        overwrite = self.query_one("#chk_overwrite", Checkbox).value
        out_dir = self.query_one("#input_out_dir", Input).value
        out_name = self.query_one("#input_out_name", Input).value

        if not target_file or not Path(target_file).exists():
            self.notify("Please select a valid file first!", severity="error")
            return

        original_path = Path(target_file)
        
        # Визначаємо фінальний шлях для збереження
        if overwrite:
            final_output_path = original_path
        else:
            save_dir = Path(out_dir) if out_dir else original_path.parent
            save_name = out_name if out_name else f"{original_path.stem}_cleaned{original_path.suffix}"
            final_output_path = save_dir / save_name

        # Блокуємо кнопку, щоб не натиснули двічі
        self.query_one("#btn_run_clean", Button).disabled = True
        
        # Відправляємо роботу у фоновий потік
        self._execute_cleaning_task(original_path, final_output_path, method)

    @work(thread=True)
    def _execute_cleaning_task(self, target_path: Path, output_path: Path, method: str) -> None:
        """Реальне виконання коду вашого бекенду у фоні."""
        try:
            # 1. Парсинг (Ваш бекенд)
            parser = RpyTranslationParser()
            dialogues = parser.parse_dialogues_only(target_path)
            
            # Якщо у process_cleaned_lines колись додасться підтримка method, 
            # ви зможете передати його сюди: process_cleaned_lines(..., method=method)
            clean_method: CleanStrategy = AVAILABLE_METHODS.get(method, AVAILABLE_METHODS["only_comment"])

            output_lines, replaced_count = TranslationCleaner(dialogues, clean_method).clean(parser.read_file(target_path))
            
            # 2. Збереження
            # (Записуємо файл напряму, щоб повністю підтримувати вибір папки з UI)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.writelines(output_lines)
            
            # Зберігаємо шлях для VS Code
            self.cleaned_file_path = str(output_path)

            # 3. Оновлення UI при успіху
            def update_ui_success():
                self.query_one("#btn_run_clean", Button).disabled = False
                self.query_one("#btn_vscode", Button).disabled = False
                self.notify(
                    f"Success! Replaced {replaced_count} duplicates.\nSaved to: {output_path.name}", 
                    title="Cleaned", timeout=5
                )
            self.app.call_from_thread(update_ui_success)

        except Exception as e:
            # Оновлення UI при помилці (щоб не залишити кнопку заблокованою назавжди)
            def update_ui_error():
                self.query_one("#btn_run_clean", Button).disabled = False
                self.notify(f"Error processing file:\n{str(e)}", severity="error", timeout=10)
            self.app.call_from_thread(update_ui_error)