from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane, Label

from translate_utils.ui.components.status_tab import StatusTab
from translate_utils.ui.components.clean_tab import CleanTab
from translate_utils.ui.components.compare_tab import CompareTab
from translate_utils.ui.components.translate_tab import TranslateTab


class ActionPanel(Static):
    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Check status", id="tab_status"):
                yield StatusTab()
            with TabPane("Clean file", id="tab_clean"):
                yield CleanTab()
            with TabPane("Compare", id="tab_compare"):
                yield CompareTab()
            with TabPane("Translate", id="tab_translate"):
                yield TranslateTab()