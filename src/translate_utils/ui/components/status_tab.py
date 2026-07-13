from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, Button
from textual.containers import VerticalScroll
from pathlib import Path

from translate_utils.utils.visualize.terminal import generate_progress_table
from translate_utils.utils.parser import get_raw_translation_data

class StatusTab(Static):
    def compose(self) -> ComposeResult:
        # yield Label("Here you can see current translation status", id="status_title")

        with VerticalScroll():
            yield Static(id="table_container")

        yield Button("Update data", id="btn_refresh_status", variant="primary")


    def on_mount(self) -> None:
        """Fires when the tab is first loaded onto the screen."""
        self._last_mtime = 0.0

        self.update_timer = self.set_interval(30.0, self.refresh_data)
        self.refresh_data()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_refresh_status":
            self.refresh_data(manual=True)
            self.update_timer.reset()

    def _get_latest_mtime(self, target_dir: Path) -> float:
        """
        Scans the directory and returns the timestamp of the most recently modified .rpy file.
        This is extremely fast compared to parsing the files.
        """
        if not target_dir.exists():
            return 0.0

        mtimes = [p.stat().st_mtime for p in target_dir.rglob("*.rpy") if p.is_file()]

        return max(mtimes, default=0.0)

    @work(thread=True)
    def refresh_data(self, manual: bool = False) -> None:
        """
        Runs in a background thread so the UI doesn't freeze while parsing files.
        """
        default_dir = Path(__file__).parents[4] / "game" / "tl" / "ukrainian"
        current_mtime = self._get_latest_mtime(default_dir)
        if not manual and current_mtime <= self._last_mtime:
            return

        self._last_mtime = current_mtime

        def update_ui(content):
            self.query_one("#table_container", Static).update(content)

        self.app.call_from_thread(update_ui, "Loading data... Please wait.")

        file_stats, global_trn, global_tot, diag_prog, str_prog = get_raw_translation_data([default_dir])
        rich_table = generate_progress_table(file_stats, global_trn, global_tot, diag_prog, str_prog)

        self.app.call_from_thread(update_ui, rich_table)

        if manual:
            self.app.call_from_thread(self.notify, "Status updated successfully!", title="Success")