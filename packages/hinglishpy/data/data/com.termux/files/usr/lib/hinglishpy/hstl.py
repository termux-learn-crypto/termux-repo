"""Hinglish Standard Library (hstl) — sab Hinglish naam me utility.

Use:
    lao hstl
    bolo hstl.muul(16)
"""
import math

# Math functions
muul = math.sqrt
gh = math.pow
paapi = math.log
floor = math.floor
ceil = math.ceil
sin = math.sin
cos = math.cos
tan = math.tan
asin = math.asin
acos = math.acos
atan = math.atan
pi = math.pi
e = math.e

# String helpers
def jodna(items, sep=","):
    """Strings ko sep se jodo."""
    return sep.join(str(x) for x in items)

def toda(s, sep=","):
    """String ko sep ke basis pe todo."""
    return s.split(sep)

def bada(s):
    """Bada (uppercase) karo."""
    return s.upper()

def chota(s):
    """Chota (lowercase) karo."""
    return s.lower()

def lam_ba(s):
    """Trim (strip) karo."""
    return s.strip()

# List helpers
def jodo(lst, item):
    """List me item add karo (append)."""
    lst.append(item)

def hatao(lst, item):
    """List se item hatao (remove)."""
    lst.remove(item)

def todo_list(iterable, size):
    """Iterable ko size ke chunks me todo."""
    it = iter(iterable)
    while True:
        chunk = list(next(it, None) for _ in range(size))
        chunk = [x for x in chunk if x is not None]
        if not chunk:
            break
        yield chunk

def merge_list(a, b):
    """Do list ko jodo (extend)."""
    a.extend(b)
