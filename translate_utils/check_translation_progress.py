from collections import defaultdict
from pathlib import Path
import argparse
from cleanup_repeats import parse_rpy_translations

def parse_args():
    parser = argparse.ArgumentParser(description="Parse Ren'Py translation files (.rpy) efficiently.")
    parser.add_argument(
        "--path", 
        type=str,
        help="Relative or Absolute Path to the .rpy translation file (e.g., ukrainian.rpy) or directory of them",
        default=None
    )
    return parser.parse_args()

def count_percentage_done(filepath: Path, info: defaultdict):
    print(f"Starting {filepath}...")
    if not filepath.suffix == ".rpy":
        print(f"Skipping {filepath.name}...")
    else:
        dialogues, menu_strings = parse_rpy_translations(filepath)
        count = 0
        for old, new in menu_strings.items():
            if old != new and not new.isascii():
                count += 1
        length = len(menu_strings)
        info[filepath.name] = count/length if length != 0 else 1

def check_translation_progress():
    info = defaultdict(float)

    args = parse_args()

    try:
        if args.path is None:
            paths = Path(__file__).parent.parent / "game" / "tl" / "ukrainian"
        else:
            paths = Path(args.path)

        if not paths.exists():
            raise ValueError(f"Wrong path, received {paths.absolute()}")

        if paths.is_file():
            count_percentage_done(paths, info)
        if paths.is_dir():
            for path in paths.iterdir():
                count_percentage_done(path, info)
        curr_percentage = 0.0
        global_percentage = 1.0 * len(info)
        print()
        for info_name, value in info.items():
            curr_percent = value * 100
            print(f"Done: {curr_percent:>6.2f}% | File name: {info_name}")
            curr_percentage += value
        global_percent = (curr_percentage / global_percentage) * 100
        print(f"Global done: {global_percent:>6.2f}%")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_translation_progress()