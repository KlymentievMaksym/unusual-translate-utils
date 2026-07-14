from textual.app import ComposeResult
from textual.widgets import Static, Label, Button

class TranslateTab(Static):
    def compose(self) -> ComposeResult:
        yield Label("Translate file", id="translate_title")
        yield Button("Translate", id="btn_do_translate", variant="primary")