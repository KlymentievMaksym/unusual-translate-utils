import concurrent.futures
from pathlib import Path
from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Button, Label, Static

from translate_utils.infrastructure.cache import CachedFileReader
from translate_utils.infrastructure.factories import create_default_progress_counter
from translate_utils.infrastructure.io import read_renpy_file
from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_TRANSLATION, gather_extension_files
from translate_utils.presentation.visualize.mixins import ProgressReportData
from translate_utils.presentation.visualize.terminal import ProgressTerminalReport
from translate_utils.services.orchestrators import BatchProgressOrchestrator
from translate_utils.services.progress_service import ProgressService


class StatusTab(Static):
    def compose(self) -> ComposeResult:
        yield Label("Translation status", id="status_title")

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
        progress_counter = create_default_progress_counter()
        progress_service = ProgressService(
            file_reader=CachedFileReader(read_renpy_file), progress_counter=progress_counter
        )
        orchestrator = BatchProgressOrchestrator(
            progress_service, lambda: concurrent.futures.ThreadPoolExecutor()
        )

        current_mtime = self._get_latest_mtime(DEFAULT_DIR_FOR_TRANSLATION)
        if not manual and current_mtime <= self._last_mtime:
            return

        self._last_mtime = current_mtime

        def update_ui(content: Any) -> None:
            self.query_one("#table_container", Static).update(content)

        self.app.call_from_thread(update_ui, "Loading data... Please wait.")

        paths_to_check = [DEFAULT_DIR_FOR_TRANSLATION]
        rpy_files = gather_extension_files(paths_to_check, "rpy")
        translation_stats = orchestrator.execute(rpy_files)

        progress_data = ProgressReportData(translation_stats)
        rich_table = ProgressTerminalReport(progress_data).generate()

        self.app.call_from_thread(update_ui, rich_table)

        if manual:
            self.app.call_from_thread(self.notify, "Status updated successfully!", title="Success")
