from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane

from translate_utils.infrastructure.saver import load_active_tab
from translate_utils.presentation.ui.components.clean_tab import CleanTab
from translate_utils.presentation.ui.components.compare_tab import CompareTab
from translate_utils.presentation.ui.components.status_tab import StatusTab
from translate_utils.presentation.ui.components.translate_tab import TranslateTab


class ActionPanel(Static):
    def compose(self) -> ComposeResult:
        with TabbedContent(initial=load_active_tab()):
            with TabPane("Check status", id="tab_status"):
                yield StatusTab()
            with TabPane("Clean file", id="tab_clean"):
                yield CleanTab()
            with TabPane("Compare", id="tab_compare"):
                yield CompareTab()
            with TabPane("Translate", id="tab_translate"):
                yield TranslateTab()
