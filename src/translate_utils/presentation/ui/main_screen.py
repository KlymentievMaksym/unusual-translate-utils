from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, TabbedContent
from textual.containers import Center, Vertical

from translate_utils.presentation.ui.base_layout import ActionPanel
from translate_utils.infrastructure.saver import save_active_tab

TABS_TITLE = "Navigation"
TAB_IDS = {
    "tab_status": {"message": "Checking status...", "title": TABS_TITLE},
    "tab_clean": {"message": "Be carefull when cleaning", "title": TABS_TITLE, "severity":"warning"},
    "tab_compare": {"message": "Choose 2 files to compare", "title": TABS_TITLE, "severity":"warning"},
    "tab_translate": {"message": "Choose file to translate", "title": TABS_TITLE, "severity":"warning"},
}
TAB_ID_FALLBACK = {"message": "Something not right", "title": TABS_TITLE, "severity":"error"}

class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main_container"):
            yield ActionPanel()

        yield Footer()

    @work(thread=True)
    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        tab_id = event.pane.id
        if tab_id is not None:
            if tab_id not in TAB_IDS:
                tab_id = "tab_status"

            save_active_tab(tab_id)
            tab_to_open = TAB_IDS.get(tab_id, TAB_ID_FALLBACK)

            self.notify(**tab_to_open) # type: ignore