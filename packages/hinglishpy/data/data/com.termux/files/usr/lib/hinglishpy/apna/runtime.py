"""Shared exec wrapper with Hinglish error reporting."""
import sys
from .error_map import describe


def run_with_hinglish_errors(code, globals_dict, args=None):
    try:
        exec(code, globals_dict)
    except SystemExit:
        raise
    except BaseException as e:
        print(describe(e))
        if args is not None:
            print(f"   File: {args.get('filename', '<unknown>')}")
        sys.exit(1)
