from textual.app import ComposeResult
from textual.widgets import Button, Label, Static


class CompareTab(Static):
    def compose(self) -> ComposeResult:
        yield Label("Compare two objects (file, files or dirs)", id="compare_title")
        yield Button("Compare", id="btn_do_compare", variant="primary")
