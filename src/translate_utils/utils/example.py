from translate_utils.utils.dataclasses import DialogueLine


def print_example(dialogues: dict[str, DialogueLine] | None = None, ui_strings: dict[str, str] | None = None):
    print("\n--- Example ---")
    if dialogues is not None:
        print("\n--- Example Dialogue Output ---")
        if "start_c16ed4c8" in dialogues:
            line_data = dialogues["start_c16ed4c8"]
            print(f"Script_pos: {line_data.script_pos}")
            print(f"Character : {line_data.character}")
            print(f"Original  : {line_data.original}")
            print(f"Translated: {line_data.translated}")

    if ui_strings is not None:
        print("\n--- Example UI Strings Output ---")
        target_string = "{sc=2}{outlinecolor=#000000}{i}But this time it is special!"
        if target_string in ui_strings:
            print(f"Original: {target_string}")
            print(f"New     : {ui_strings[target_string]}")