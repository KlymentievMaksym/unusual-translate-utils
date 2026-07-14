from pathlib import Path

def save_lines_to_file(original_filepath: str | Path, text_to_replace_with: str, new_name: str | Path | None = None) -> Path:
    original_path = Path(original_filepath)

    if new_name is None:
        out_filepath = original_path
    else:
        new_name = Path(new_name)
        out_filepath = original_path.with_name(f"{new_name}{original_path.suffix}")

    with open(out_filepath, 'w', encoding='utf-8') as f:
        f.write(text_to_replace_with)

    return out_filepath