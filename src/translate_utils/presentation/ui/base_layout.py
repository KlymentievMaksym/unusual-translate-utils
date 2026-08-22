from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane

from translate_utils.infrastructure.saver import load_active_tab
from translate_utils.presentation.ui.components.clean_tab import CleanTab
from translate_utils.presentation.ui.components.compare_tab import CompareTab
from translate_utils.presentation.ui.components.status_tab import StatusTab
from translate_utils.presentation.ui.components.translate_tab import TranslateTab


class ActionPanel(Static):
    def compose(self) -> ComposeResult:
        with TabbedContent(initial=load_active_tab(), id="tabs"):
            with TabPane("Check status", id="tab_status", classes="tabs"):
                yield StatusTab()
            with TabPane("Clean file", id="tab_clean", classes="tabs"):
                yield CleanTab()
            with TabPane("Compare", id="tab_compare", classes="tabs"):
                yield CompareTab()
            with TabPane("Translate", id="tab_translate", classes="tabs"):
                yield TranslateTab()
