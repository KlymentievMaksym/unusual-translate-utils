from textual.app import App

from translate_utils.infrastructure.filesystem.path import initialize_config
from translate_utils.infrastructure.logging.logger import get_logger, setup_logging
from translate_utils.presentation.ui.main_screen import MainScreen

LOGGER = get_logger("GW-Translate")


class GWTranslateApp(App[None]):
    CSS_PATH = "styles/global.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def on_mount(self) -> None:
        config = initialize_config()
        setup_logging("GW-Translate", config.paths.common_logs_dir)
        LOGGER.info("Started TUI")
        self.push_screen(MainScreen(config))


if __name__ == "__main__":
    app = GWTranslateApp()
    app.run()
