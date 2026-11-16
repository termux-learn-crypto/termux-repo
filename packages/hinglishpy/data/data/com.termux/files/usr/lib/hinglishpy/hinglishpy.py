# HinglishPy CLI - hinglishpy command
import sys
import os
from compiler import compile_code
from apna.importer import add_script_dir
from apna.runtime import run_with_hinglish_errors

VERSION = "3.6.0"

USAGE = """HinglishPy 3.6.0 - Python jaisa, par Hinglish me

Usage:
  hinglishpy                  Interactive REPL (hinglishpy >>> )
  hinglishpy script.hl        .hl file chalana
  hinglishpy script.hl a b    .hl file chalana, args sys.argv me milenge
  hinglishpy -c "code"        Seedha code chalana
  hinglishpy --help           Ye help
  hinglishpy --version        Version batana

Examples:
  hinglishpy hello.hl
  hinglishpy -c 'bolo "Namaste duniya!"'
  hinglishpy -c 'bolo ginti(5)'
"""

def run_source(source, argv, filename=None):
    python_code = compile_code(source)
    sys.argv = argv
    run_with_hinglish_errors(python_code, {"__name__": "__main__"}, {"filename": filename or "<c>"})

HINGLISH_WORDS = [
    "agar", "nahito", "warna", "anyatha", "jabtak", "har", "me", "kaam", "varg",
    "wapas", "koshish", "pakdo", "ant", "lao", "se", "jaise", "todo", "jaari",
    "chhodo", "badhao", "saath", "banao", "sach", "mitao", "batao", "asink",
    "intezar", "baishvik", "asthaniye", "bolo", "puchho", "khud",
    "sahi", "galat", "kuchnahi", "aur", "ya", "nahi", "hai", "lambai",
    "ginti", "kramank", "yog", "nyuntam", "adhiktam", "pariman", "gol", "ghat",
    "krambadh", "ulta", "samuh", "suchi", "shabdkosh", "yugm", "shabd", "ank",
    "akshar", "pehchan", "prakar", "bahar",
]

try:
    import readline

    def complete(text, state):
        matches = [w for w in HINGLISH_WORDS if w.startswith(text)]
        return matches[state] if state < len(matches) else None

    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t")
except Exception:
    pass

def repl():
    print(f"HinglishPy {VERSION} - Apna Compiler, Poora Hinglish Me")
    print("Bahar nikalne ke liye: bahar | Ctrl+C se line cancel")
    print("")
    my_vars = {}
    pending = []
    while True:
        if pending:
            line = pending.pop()
        else:
            try:
                line = input("hinglishpy >>> ")
            except (EOFError, KeyboardInterrupt):
                print("\nAlvida!")
                break
        stripped = line.strip()
        if stripped in ["bahar", "exit", "quit"] and not pending:
            print("Alvida!")
            break
        if stripped == "":
            continue
        if stripped.endswith(":"):
            lines = [line]
            first_indent = None
            while True:
                try:
                    nxt = input("... ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    lines = None
                    break
                ns = nxt.strip()
                nxt_indent = (len(nxt) - len(nxt.lstrip())) if ns else None
                if nxt_indent is None:
                    break
                if first_indent is None:
                    if nxt_indent == 0:
                        pending.insert(0, nxt)
                        break
                    first_indent = nxt_indent
                elif nxt_indent == 0:
                    pending.insert(0, nxt)
                    break
                lines.append(nxt)
            if lines is None:
                print("(cancel)")
                continue
            full_code = "\n".join(lines)
        else:
            full_code = line
        try:
            python_code = compile_code(full_code)
            run_with_hinglish_errors(python_code, my_vars, {})
        except SystemExit:
            continue
        except BaseException as e:
            print(f"Galti / Error: {e}")

def main():
    args = sys.argv[1:]
    if not args:
        add_script_dir(os.getcwd())
        repl()
        return
    if args[0] in ("-h", "--help"):
        print(USAGE)
        return
    if args[0] == "--version":
        print(f"HinglishPy {VERSION}")
        return
    if args[0] == "-c":
        if len(args) < 2:
            print("hinglishpy: -c requires an argument")
            sys.exit(2)
        add_script_dir(os.getcwd())
        run_source(args[1], ["-c"] + args[2:], "-c")
        return
    script = args[0]
    if not script.endswith(".hl"):
        print(f"hinglishpy: {script} — file .hl honi chahiye")
        print("hinglishpy --help")
        sys.exit(2)
    try:
        with open(script, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"hinglishpy: File nahi mili - {script}")
        sys.exit(2)
    add_script_dir(script)
    run_source(source, [script] + args[1:], script)

if __name__ == "__main__":
    main()
