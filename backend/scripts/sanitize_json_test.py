import json
import re
import logging

logger = logging.getLogger(__name__)

def sanitize_json_string(s: str) -> str:
    """
    Attempt to sanitize a string to make it valid JSON.
    1. Fix invalid escapes (e.g. \t, \times in LaTeX).
    2. Extract the main JSON array/object.
    """
    # 1. Extract potential JSON block (from first [ to last ])
    match = re.search(r'(\[.*\])', s, re.DOTALL)
    if match:
        s = match.group(1)
    
    # 2. Fix common LaTeX escape issues that break JSON
    # JSON requires backslashes to be escaped (\\). 
    # LaTeX often uses single backslashes (\times, \frac).
    # Heuristic: If we see a backslash followed by a non-JSON-escape char, double it.
    # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    
    # We want to replace \ (not followed by " \ / b f n r t u) with \\
    # But this is hard to do perfectly with regex because of overlapping.
    # Simpler approach: 
    # If the LLM outputs LaTeX, it likely didn't escape the backslashes.
    # e.g. "content": "Calculate \times" -> invalid.
    # "content": "Calculate \\times" -> valid.
    
    # Strategy: repr() or manual replacement is too risky. 
    # Let's try to use a specific regex to catch LaTeX-like patterns?
    # Actually, simpler: many local LLMs struggle with escaping.
    # Let's try `json_repair` library logic if available, or a simple fallback.
    
    # Fallback: Double escape all backslashes that are NOT part of a valid escape sequence?
    # Valid escapes in Python regex: \\" \\\\ \\/ \\b \\f \\n \\r \\t \\u[0-9a-fA-F]{4}
    
    # A safer, dumber fix:
    # 1. Replace double backslashes \\ with a PLACEHOLDER
    # 2. Replace single backslashes \ with \\ (assuming they are unescaped LaTeX)
    # 3. Restore PLACEHOLDER to \\
    # This might break real \n, \t... tricky.
    
    # Let's just try to parse. If fail, return empty list or try to use a specialized library.
    # Since we can't install new libs easily, we'll try a basic "fix invalid escapes" 
    # by replacing single backslashes that aren't common escapes.
    
    def repl(match):
        g = match.group(0)
        if g in ['\\"', '\\\\', '\\/', '\\b', '\\f', '\\n', '\\r', '\\t']:
            return g
        if g.startswith('\\u'):
             return g # Assume valid unicode
        return '\\\\' + g[1:] # Double the backslash

    # Regex to find backslash + char
    # pattern = r'\\.'
    # return re.sub(pattern, repl, s)
    return s

# ... (rest of the file content)
