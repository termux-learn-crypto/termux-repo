import re
from collections import namedtuple
from .errors import HinglishError

Token = namedtuple("Token", ["type", "value", "line"])

KEYWORDS = {
    "agar": "IF", "nahito": "ELIF", "warna": "ELSE", "anyatha": "ELSE",
    "jabtak": "WHILE", "har": "FOR", "me": "IN",
    "kaam": "DEF", "varg": "CLASS", "wapas": "RETURN",
    "sahi": "TRUE", "galat": "FALSE", "kuchnahi": "NONE",
    "aur": "AND", "ya": "OR", "nahi": "NOT", "hai": "IS",
    "koshish": "TRY", "pakdo": "EXCEPT", "ant": "FINALLY",
    "lao": "IMPORT", "se": "FROM", "jaise": "AS",
    "todo": "BREAK", "jaari": "CONTINUE", "chhodo": "PASS",
    "badhao": "RAISE", "saath": "WITH", "banao": "LAMBDA",
    "sach": "ASSERT", "mitao": "DEL", "batao": "YIELD",
    "baishvik": "GLOBAL", "asthaniye": "NONLOCAL",
    "intezar": "AWAIT", "asink": "ASYNC", "bolo": "PRINT",
    "match": "MATCH", "case": "CASE",
}

_NUMBER = (
    r"(?:\d[\d_]*(?:\.[\d_]*\d|[\d_]*\.\d)?(?:[eE][+-]?[\d_]+)?[jJ]?"
    r"|0[xX][0-9a-fA-F_]+[jJ]?"
    r"|0[bB][01_]+[jJ]?"
    r"|0[oO][0-7_]+[jJ]?)"
)

_STRING = (
    r"(?i:fr|rb|br|rf|f|r|b)?"
    r"(?:\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''"
    r"|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')"
)

_NAME = r"[A-Za-z_][A-Za-z0-9_]*"

_OPS = [
    "**=", "//=", "<<=", ">>=", "@=", "->", ":=",
    "**", "//", "<<", ">>", "<=", ">=", "==", "!=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
    "+", "-", "*", "/", "%", "@", "~", "&", "|", "^", "<", ">", "=", ":", ",", "(", ")", "[", "]", "{", "}", ".",
]
_OPS.sort(key=len, reverse=True)
_OP_PATTERN = "|".join(re.escape(o) for o in _OPS)

_MASTER = re.compile(
    r"(?P<string>" + _STRING + r")"
    r"|(?P<number>" + _NUMBER + r")"
    r"|(?P<name>" + _NAME + r")"
    r"|(?P<comment>\#[^\n]*)"
    r"|(?P<op>" + _OP_PATTERN + r")"
    r"|(?P<ws>[ \t]+)"
    r"|(?P<newline>\n)"
    r"|(?P<other>.)"
)

def logical_lines(src):
    """Source ko logical lines me todo (bracket join + triple string support).
    Returns: list of (start_line, text)."""
    phys = src.split("\n")
    out = []
    i = 0
    n = len(phys)
    while i < n:
        start_line = i + 1
        buf = []
        depth = 0
        triple = None
        while i < n:
            raw = phys[i]
            j = 0
            m = len(raw)
            while j < m:
                ch = raw[j]
                if triple:
                    k = raw.find(triple, j)
                    if k == -1:
                        buf.append(raw[j:])
                        j = m
                    else:
                        buf.append(raw[j:k + 3])
                        j = k + 3
                        triple = None
                    continue
                if raw.startswith('"""', j):
                    triple = '"""'
                    buf.append('"""')
                    j += 3
                    continue
                if raw.startswith("'''", j):
                    triple = "'''"
                    buf.append("'''")
                    j += 3
                    continue
                if ch == '"' or ch == "'":
                    k = j + 1
                    while k < m:
                        c = raw[k]
                        if c == '\\':
                            k += 2
                            continue
                        if c == ch:
                            k += 1
                            break
                        k += 1
                    else:
                        raise HinglishError(i + 1, "String band nahi hui", "Unterminated string literal")
                    buf.append(raw[j:k])
                    j = k
                    continue
                if ch == '#':
                    j = m
                    break
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                    if depth < 0:
                        raise HinglishError(i + 1, "Bracket zyada band ho gayi", "Too many closing brackets")
                buf.append(ch)
                j += 1
            if triple:
                buf.append("\n")
                i += 1
                continue
            if depth == 0:
                out.append((start_line, "".join(buf)))
                i += 1
                break
            else:
                buf.append("\n")
                i += 1
        else:
            if triple:
                raise HinglishError(start_line, "Triple string band nahi hui", "Unterminated triple-quoted string")
    return out

def tokenize(src):
    tokens = []
    indent_stack = [0]

    for start_line, logical in logical_lines(src):
        stripped = logical.strip()
        if not stripped or stripped.startswith("#"):
            continue

        raw_first = logical.split("\n", 1)[0]
        indent = 0
        for ch in raw_first:
            if ch == ' ':
                indent += 1
            elif ch == '\t':
                raise HinglishError(start_line, "Indent mein tab hai", "Tab in indentation")
            else:
                break

        top = indent_stack[-1]
        if indent > top:
            indent_stack.append(indent)
            tokens.append(Token("INDENT", "", start_line))
        elif indent < top:
            while indent_stack[-1] > indent:
                indent_stack.pop()
                tokens.append(Token("DEDENT", "", start_line))
            if indent_stack[-1] != indent:
                raise HinglishError(start_line,
                                     "Indent Python jaisa nahi hai",
                                     "Inconsistent indentation")

        line_no = start_line
        for mo in _MASTER.finditer(logical):
            if mo.lastgroup == "newline":
                continue
            kind = mo.lastgroup
            text = mo.group()
            embedded_nl = text.count("\n")
            if kind == "string":
                tokens.append(Token("STRING", text, line_no))
            elif kind == "number":
                tokens.append(Token("NUMBER", text, line_no))
            elif kind == "name":
                kw = KEYWORDS.get(text)
                tokens.append(Token(kw if kw else "NAME", text, line_no))
            elif kind == "comment":
                pass
            elif kind == "op":
                tokens.append(Token(text, text, line_no))
            elif kind == "other":
                raise HinglishError(line_no, f"Achuuk character: {text!r}", f"Unknown character: {text!r}")
            line_no += embedded_nl
        tokens.append(Token("NEWLINE", "", line_no))

    last_line = src.count("\n") + 1
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token("DEDENT", "", last_line))
    tokens.append(Token("EOF", "", last_line))
    return tokens
