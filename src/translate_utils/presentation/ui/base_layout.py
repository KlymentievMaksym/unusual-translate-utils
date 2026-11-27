from rich.console import ConsoleRenderable, RichCast
from textual.app import ComposeResult
from textual.visual import SupportsVisual, Visual
from textual.widgets import Static, TabbedContent, TabPane

from translate_utils.infrastructure.filesystem.path import AppConfig
from translate_utils.presentation.ui.components.clean_tab import CleanTab
from translate_utils.presentation.ui.components.compare_tab import CompareTab
from translate_utils.presentation.ui.components.status_tab import StatusTab
from translate_utils.presentation.ui.components.translate_tab import TranslateTab


class ActionPanel(Static):
    def __init__(
        self,
        config: AppConfig,
        content: ConsoleRenderable | RichCast | str | SupportsVisual | Visual = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self._config = config

    def compose(self) -> ComposeResult:
        with TabbedContent(initial=self._config.settings.active_tab, id="tabs"):
            with TabPane("Check status", id="tab_status", classes="tabs"):
                yield StatusTab(self._config)
            with TabPane("Clean file", id="tab_clean", classes="tabs"):
                yield CleanTab()
            with TabPane("Compare", id="tab_compare", classes="tabs"):
                yield CompareTab()
            with TabPane("Translate", id="tab_translate", classes="tabs"):
                yield TranslateTab()
