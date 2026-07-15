from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, Button
from textual.containers import VerticalScroll
from pathlib import Path

from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_TRANSLATION
from translate_utils.presentation.visualize.terminal import ProgressReportData, ProgressTerminalReport

from translate_utils.infrastructure.parser import RpyTranslationParser
from translate_utils.services.progress_service import ProgressService

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
        """Runs in a background thread so the UI doesn't freeze while parsing files."""
        parser = RpyTranslationParser()
        progress_checker = ProgressService(parser)

        current_mtime = self._get_latest_mtime(DEFAULT_DIR_FOR_TRANSLATION)
        if not manual and current_mtime <= self._last_mtime:
            return

        self._last_mtime = current_mtime

        def update_ui(content):
            self.query_one("#table_container", Static).update(content)

        self.app.call_from_thread(update_ui, "Loading data... Please wait.")

        raw_data = progress_checker.get_raw_translation_data([DEFAULT_DIR_FOR_TRANSLATION])
        if raw_data is None:
            return

        file_stats, global_trn, global_tot, diag_prog, str_prog = raw_data
        rich_table = ProgressTerminalReport(ProgressReportData(file_stats, global_trn, global_tot, diag_prog, str_prog)).generate()

        self.app.call_from_thread(update_ui, rich_table)

        if manual:
            self.app.call_from_thread(self.notify, "Status updated successfully!", title="Success")