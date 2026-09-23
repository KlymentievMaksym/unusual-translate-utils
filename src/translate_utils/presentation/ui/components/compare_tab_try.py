import difflib
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, TextArea, Tree

from translate_utils.infrastructure.factories import create_default_parser
from translate_utils.infrastructure.io import read_renpy_file
from translate_utils.services.compare_service import CompareService, DirectoryCompareResult


class CompareTreeApp(App[None]):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    _dir_f = "dir1"
    _dir_s = "dir2"
    _compare = "compare"
    _btn = "btn-"
    _btn_compare = _btn + _compare
    _btn_f = _btn + _dir_f
    _btn_s = _btn + _dir_s
    _inpt = "input-"
    _inpt_f = _inpt + _dir_f
    _inpt_s = _inpt + _dir_s

    def __init__(self, compare_service: CompareService | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.compare_service = compare_service

    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            with Horizontal(id="top-section"):
                with Vertical(id="buttons-container", classes="container"):
                    yield Label("Choose 2 directories to compare")
                    with Horizontal():
                        yield Button("Directory 1", id=self._btn_f, variant="primary")
                        yield Input(placeholder="Path to directory...", id=self._inpt_f)
                    with Horizontal():
                        yield Button("Directory 2", id=self._btn_s, variant="primary")
                        yield Input(placeholder="Path to directory...", id=self._inpt_s)
                    yield Button("Compare", id=self._btn_compare, variant="warning", disabled=True)

                with Vertical(id="tree-container", classes="container"):
                    yield Label("Compare results:")
                    yield Tree("Files", id="diff-tree")

            with Horizontal(id="bottom-section"):
                yield TextArea(
                    "Виберіть файл для перегляду...",
                    id="text-file1",
                    classes="text-column",
                    read_only=True,
                )
                yield TextArea(
                    "Виберіть файл для перегляду...",
                    id="text-file2",
                    classes="text-column",
                    read_only=True,
                )

    def on_mount(self) -> None:
        tree = self.query_one("#diff-tree", Tree)
        tree.show_root = False
        self.added_node = tree.root.add("🟩 Додані файли", expand=True)
        self.changed_node = tree.root.add("🟨 Змінені файли", expand=True)
        self.deleted_node = tree.root.add("🟥 Видалені файли", expand=True)
        self.identical_node = tree.root.add("⬛ Ідентичні файли", expand=False)

    @on(Button.Pressed, f"#{_btn_f}")
    def select_dir1(self) -> None:
        self.notify("Вибір Directory 1")
        self.open_explorer(self._inpt_f)
        self.check_if_dir_selected()

    @on(Button.Pressed, f"#{_btn_s}")
    def select_dir2(self) -> None:
        self.notify("Вибір Directory 2")
        self.open_explorer(self._inpt_s)
        self.check_if_dir_selected()

    @on(Button.Pressed, f"#{_btn_compare}")
    def run_compare(self) -> None:
        dir1 = self.query_one(f"#{self._inpt_f}", Input).value
        dir2 = self.query_one(f"#{self._inpt_s}", Input).value

        self.notify("Аналіз файлів та парсинг діалогів...", severity="warning")
        self.query_one(
            f"#{self._btn_compare}", Button
        ).disabled = True  # Блокуємо від подвійного кліку

        # Запускаємо важку роботу у Worker
        self.compare_directories_task(dir1, dir2)

    @work(thread=True)
    def compare_directories_task(self, dir1: str, dir2: str) -> None:
        """Worker для виконання важких обчислень без блокування UI"""
        if not self.compare_service:
            self.app.call_from_thread(
                self.notify, "Compare service is not initialized", severity="error"
            )
            return

        # Виконуємо парсинг і порівняння структур даних
        result = self.compare_service.compare_directories(dir1, dir2)

        # Безпечно оновлюємо UI з потоку
        self.app.call_from_thread(self.update_tree_ui, result)

    def update_tree_ui(self, result: "DirectoryCompareResult") -> None:
        """Оновлює дерево результатами порівняння"""
        # Очищаємо попередні результати
        self.added_node.remove_children()
        self.changed_node.remove_children()
        self.deleted_node.remove_children()
        self.identical_node.remove_children()

        for f in result.added:
            self.added_node.add_leaf(f)
        for f in result.changed:
            self.changed_node.add_leaf(f)
        for f in result.deleted:
            self.deleted_node.add_leaf(f)
        for f in result.identical:
            self.identical_node.add_leaf(f)

        self.query_one(f"#{self._btn_compare}", Button).disabled = False
        self.notify("Порівняння завершено!", severity="information")

    @on(Tree.NodeSelected, "#diff-tree")
    def update_text_areas(self, event: Tree.NodeSelected[None]) -> None:
        if event.node.allow_expand:
            return

        selected_file = str(event.node.label)
        dir1 = self.query_one(f"#{self._inpt_f}", Input).value
        dir2 = self.query_one(f"#{self._inpt_s}", Input).value

        text_file1 = self.query_one("#text-file1", TextArea)
        text_file2 = self.query_one("#text-file2", TextArea)

        path1 = Path(dir1) / selected_file
        path2 = Path(dir2) / selected_file

        if path1.exists():
            text_file1.text = "text"
        else:
            text_file1.text = "File not exists in Directory 1 (Deleted)"

        if path2.exists():
            text_file2.text = "text"
        else:
            text_file2.text = "File not exists in Directory 2 (Deleted)"

    def check_if_dir_selected(self) -> None:
        button = self.query_one(f"#{self._btn_compare}", Button)
        first_value = self.query_one(f"#{self._inpt_f}", Input).value
        second_value = self.query_one(f"#{self._inpt_s}", Input).value

        button.disabled = not (bool(first_value) and bool(second_value))

    @work(thread=True)
    def open_explorer(self, id: str) -> None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        dir_path = filedialog.askdirectory(title="Select a Directory", initialdir="/")
        root.destroy()
        if dir_path:

            def update_input() -> None:
                self.query_one(f"#{id}", Input).value = dir_path

            self.app.call_from_thread(update_input)

    def compare(self) -> None:
        pass


if __name__ == "__main__":
    app = CompareTreeApp(
        CompareService(
            file_reader=,
            file_parser=create_default_parser(),
            file_cleaner=
        )
    )
    app.run()
