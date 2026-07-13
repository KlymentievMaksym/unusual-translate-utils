from textual.app import App
from translate_utils.ui.main_screen import MainScreen

class GWTranslateApp(App):
    CSS_PATH = "ui/styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit")
    ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

if __name__ == "__main__":
    app = GWTranslateApp()
    app.run()