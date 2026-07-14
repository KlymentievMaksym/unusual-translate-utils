import re

RE_TRANSLATE_BLOCK = re.compile(
    r'^\s*#\s*(?:.*?[/\\])?([^/\\]+\.rpy:\d+)\n'  # 1 - script in game position
    r'^translate\s+\w+\s+(\w+):\n'               # 2 - script label
    r'^\s*#\s*(?:(\w+)\s+)?\"(.*?)\"$\n'          # 3 - character; 4 - original text
    r'^\s*(?:(\w+)\s+)?\"(.*?)\"$',               # 5 - character; 6 - translated text
    re.MULTILINE | re.DOTALL
)
RE_STRINGS_BLOCK = re.compile(
    # r'^((?:\s*#.*?\n)+)?'  # 1 - comment
    r'^([ \t]+)old\s+("""|")(.*?)(?<!\\)\2'       # 1 - indent; 2 - " or """; 3 - old text
    r'.*?'
    r'\n\1new\s+("""|")(.*?)(?<!\\)\4',           # 4 - " or """; 5 - new text
    re.MULTILINE | re.DOTALL
)
