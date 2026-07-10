from pathlib import Path

def save_lines_to_file(original_filepath: str | Path, output_lines: list[str], new_name: str | None = None) -> Path:
    """
    Writes a list of string lines to a file. 
    Appends '_cleaned' to the filename if is_same_name is False.
    """
    original_path = Path(original_filepath)
    
    if new_name is None:
        out_filepath = original_path
    else:
        out_filepath = original_path.with_name(f"{new_name}{original_path.suffix}")

    with open(out_filepath, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
        
    return out_filepath