from textual.app import App

from translate_utils.infrastructure.logger import setup_logging
from translate_utils.presentation.ui.main_screen import MainScreen

LOGGER = setup_logging("GW-Translate")


class GWTranslateApp(App[None]):
    CSS_PATH = "presentation/ui/styles.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def on_mount(self) -> None:
        LOGGER.info("Started")
        self.push_screen(MainScreen())


if __name__ == "__main__":
    app = GWTranslateApp()
    app.run()
