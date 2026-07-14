import re

RE_TRANSLATE_BLOCK = re.compile(
    r'^\s*#\s*(?:.*[/\\])?([^/\\]+\.rpy:\d+)\n'  # 1 - script in game position
    r'^translate\s+\w+\s+(\w+):\n'               # 2 - script label
    r'^\s*#\s*(?:(\w+)\s+)?\"(.*)\"$\n'          # 3 - character; 4 - original text
    r'^\s*(?:(\w+)\s+)?\"(.*)\"$',               # 5 - character; 6 - translated text
    re.MULTILINE | re.DOTALL
)
RE_STRINGS_BLOCK = re.compile(
    r'^([ \t]+)old\s+("""|")(.*?)\2'  # 1 - indent; 2 - " or """; 3 - old text
    r'.*?'
    r'\n\1new\s+("""|")(.*?)\4',      # 4 - " or """; 5 - new text
    re.MULTILINE | re.DOTALL
)

# RE_LABEL = re.compile(r'^translate\s+\w+\s+(\w+):')
# RE_STRINGS_BLOCK = re.compile(r'^translate\s+\w+\s+strings:')

# RE_SCRIPT_POS = re.compile(r'^\s*#\s*(?:.*[/\\])?([^/\\]+\.rpy:\d+)')
# RE_COMMENT_TEXT = re.compile(r'^\s*#\s*(?:(\w+)\s+)?\"(.*)\"$')
# RE_ACTIVE_TEXT = re.compile(r'^\s*(?:(\w+)\s+)?\"(.*)\"$')

# RE_OLD = re.compile(r'^(\s*)old\s+("""|")(.*)\2$', re.DOTALL)
# RE_NEW = re.compile(r'^(\s*)new\s+("""|")(.*)\2$', re.DOTALL)

# RE_OLD_SINGLE = re.compile(r'^(\s*)old\s+\"(.*)\"$')
# RE_NEW_SINGLE = re.compile(r'^\s*new\s+\"(.*)\"$')

# RE_OLD_MULTI = re.compile(r'^(\s)*old\s+\"\"\"')
# RE_NEW_MULTI = re.compile(r'^\s*new\s+\"\"\"')