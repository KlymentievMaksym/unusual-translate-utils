from textual.app import ComposeResult
from textual.widgets import Static, Label, Button

class CleanTab(Static):
    def compose(self) -> ComposeResult:
        yield Label("Clean file from repeats")
        yield Button("Clean file", id="btn_run_clean", variant="error")