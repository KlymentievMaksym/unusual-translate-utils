from typing import Literal, TypedDict

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, TabbedContent

from translate_utils.infrastructure.saver import save_active_tab
from translate_utils.presentation.ui.base_layout import ActionPanel


class NotificationConfig(TypedDict, total=False):
    message: str
    title: str
    severity: Literal["information", "warning", "error"]

TABS_TITLE = "Navigation"

TAB_NOTIFICATIONS: dict[str, NotificationConfig] = {
    "tab_status": {"message": "Checking status...", "title": TABS_TITLE},
    "tab_clean": {
        "message": "Be careful when cleaning",
        "title": TABS_TITLE,
        "severity": "warning",
    },
    "tab_compare": {
        "message": "Choose 2 files to compare",
        "title": TABS_TITLE,
        "severity": "warning",
    },
    "tab_translate": {
        "message": "Choose file to translate",
        "title": TABS_TITLE,
        "severity": "warning",
    },
}

TAB_ID_FALLBACK: NotificationConfig = {
    "message": "Something not right",
    "title": TABS_TITLE,
    "severity": "error"
}


class MainScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main_container"):
            yield ActionPanel()
        yield Footer()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        tab_id = event.pane.id

        if not tab_id:
            tab_id = "unknown_tab"

        save_active_tab(tab_id)

        notification = TAB_NOTIFICATIONS.get(tab_id, TAB_ID_FALLBACK)

        self.notify(**notification)
