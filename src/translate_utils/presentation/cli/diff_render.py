# translate_utils/presentation/cli/diff_render.py

import difflib
import shutil
import subprocess

from rich.console import Console, Group
from rich.pager import Pager
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from translate_utils.services.diff_service import ChangeEntry, DiffResult

console = Console()

SEVERITY_STYLE = {
    "major": "bold red",
    "minor": "yellow",
    "added": "green",
    "removed": "dim red",
}

SEVERITY_ORDER = ("major", "minor", "added", "removed")


class Utf8Pager(Pager):
    """Pipes to `less -R` with explicit UTF-8 encoding, avoiding pydoc's
    ascii-backslashreplace fallback that mangles non-ASCII text."""

    def show(self, content: str) -> None:
        pager_cmd = shutil.which("less") or shutil.which("more")
        if pager_cmd is None:
            # no external pager available — just print directly
            print(content)
            return

        args = [pager_cmd, "-R"] if "less" in pager_cmd else [pager_cmd]
        try:
            proc = subprocess.Popen(args, stdin=subprocess.PIPE, encoding="utf-8")
            proc.communicate(content)
        except (BrokenPipeError, OSError):
            print(content)

def _word_diff(old: str | None, new: str | None) -> Text:
    old_words = (old or "").split()
    new_words = (new or "").split()
    matcher = difflib.SequenceMatcher(None, old_words, new_words)
    text = Text()
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            text.append(" ".join(old_words[i1:i2]) + " ")
        elif op == "replace":
            text.append(" ".join(old_words[i1:i2]) + " ", style="strike red")
            text.append(" ".join(new_words[j1:j2]) + " ", style="bold green")
        elif op == "delete":
            text.append(" ".join(old_words[i1:i2]) + " ", style="strike red")
        elif op == "insert":
            text.append(" ".join(new_words[j1:j2]) + " ", style="bold green")
    return text


def render_summary(filepath: str, dial_diff: DiffResult, str_diff: DiffResult) -> Table:
    table = Table(title=f"Summary: {filepath}", show_header=True, header_style="bold")
    table.add_column("Category")
    for sev in SEVERITY_ORDER:
        table.add_column(sev.capitalize(), justify="right", style=SEVERITY_STYLE[sev])

    table.add_row("Dialogues", *[str(len(getattr(dial_diff, sev))) for sev in SEVERITY_ORDER])
    table.add_row("Strings", *[str(len(getattr(str_diff, sev))) for sev in SEVERITY_ORDER])
    return table


def render_entries(source_name: str, severity: str, entries: list[ChangeEntry]) -> Panel | None:
    if not entries:
        return None

    lines = []
    for entry in entries:
        lines.append(Text(f"[{entry.key}]", style="bold"))
        if severity in ("added", "removed"):
            lines.append(Text(entry.new_text or entry.old_text or "", style=SEVERITY_STYLE[severity]))
        else:
            lines.append(_word_diff(entry.old_text, entry.new_text))
        lines.append(Text(""))

    return Panel(
        Group(*lines),
        title=f"{source_name} — {severity} ({len(entries)})",
        border_style=SEVERITY_STYLE[severity],
        expand=False,
    )


def render_diff(filepath: str, dial_diff: DiffResult, str_diff: DiffResult, show: set[str] | None = None) -> None:
    show = show if show is not None else {"major", "minor"}

    with console.pager(pager=Utf8Pager(), styles=True):
        console.print(render_summary(filepath, dial_diff, str_diff))
        for source_name, diff in (("Dialogues", dial_diff), ("Strings", str_diff)):
            for severity in SEVERITY_ORDER:
                if severity not in show:
                    continue
                panel = render_entries(source_name, severity, getattr(diff, severity))
                if panel:
                    console.print(panel)
