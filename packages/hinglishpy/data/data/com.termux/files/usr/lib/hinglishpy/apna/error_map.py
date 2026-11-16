"""Python runtime errors → Hinglish messages."""
import re

_MESSAGES = [
    (NameError, r"name '(.+?)' is not defined",
     "Variable '{}' defined nahi hai"),
    (NameError, r"name '(.+?)' is not defined",
     "Yeh naam program me kahi use nahi hota: '{}'"),

    (ZeroDivisionError, r"integer division or modulo by zero",
     "0 se bhag ya remainder nahi nikaal sakte"),
    (ZeroDivisionError, r"division by zero",
     "0 se bhag nahi sakte"),

    (IndexError, r"list index out of range",
     "List ka index range se bahar hai"),
    (IndexError, r"index out of range",
     "Index range ke bahar hai"),

    (KeyError, r"^'(.+?)'$",
     "Dictionary me key nahi mili: '{}'"),
    (KeyError, r"^(.+)$",
     "Dictionary me key nahi mili: {}"),

    (AttributeError, r"'(.+?)' object has no attribute '(.+?)'",
     "'{}' object me '{}' naam ka attribute nahi hai"),
    (AttributeError, r"module '(.+?)' has no attribute '(.+?)'",
     "Module '{}' me '{}' nahi hai"),

    (ValueError, r"invalid literal for (.+?)\(\)",
     "Value galat format me hai: {}"),
    (ValueError, r"not enough values to unpack",
     "Values kam hain unpack karne ke liye"),
    (ValueError, r"too many values to unpack",
     "Values zyada hain unpack karne ke liye"),

    (ImportError, r"No module named '(.+?)'",
     "Module '{}' nahi mila — install gara? (pip install {})"),
    (ImportError, r"cannot import name '(.+?)'",
     "Import nahi ho paya: '{}' module me nahi hai"),

    (FileNotFoundError, r"No such file or directory: '(.+?)'",
     "File ya folder nahi mili: '{}'"),

    (TypeError, r"missing (\d+) required positional argument",
     "Function ko {} zaruri argument chahiye — kam diya"),
    (TypeError, r"takes (\d+) positional argument",
     "Function sirf {} positional argument leta hai — zyada diya"),
    (TypeError, r"unsupported operand type\(s\) for (.+?): '(.+?)' and '(.+?)'",
     "'{}' ke liye '{}' aur '{}' compatible nahi hain"),

    (SyntaxError, r".*",
     "Syntax me galti hai — dekho ga part matlab galat hai"),
]


def translate(error):
    """Hinglish message for common Python exceptions. None if unknown."""
    msg = str(error)
    for exc_type, pattern, template in _MESSAGES:
        if not isinstance(error, exc_type):
            continue
        m = re.match(pattern, msg)
        if m:
            return template.format(*m.groups())
    return None


def describe(error):
    """Full traceback → Hinglish-prefixed message."""
    translated = translate(error)
    if translated:
        return f"[HinglishPy Galti] {translated}"
    return f"[HinglishPy Galti] {type(error).__name__}: {error}"
