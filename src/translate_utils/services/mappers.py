from collections import defaultdict
from typing import Mapping

from translate_utils.core.entities import DialogueLine


def build_reverse_lookup(dialogues: Mapping[str, DialogueLine]) -> dict[str, tuple[str, ...]]:
    """
    Builder function to decouple Domain Entities from the text processing engine.
    """
    lookup: defaultdict[str, list[str]] = defaultdict(list)

    for data in dialogues.values():
        if data.original_text and data.script_position:
            lookup[data.original_text].append(data.script_position)

    return {text: tuple(positions) for text, positions in lookup.items()}
