# HinglishPy CLI - hinglishpy command
import sys
from compiler import compile_code

VERSION = "3.4.0"

USAGE = """HinglishPy 3.4.0 - Python jaisa, par Hinglish me

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

def run_source(source, argv):
    python_code = compile_code(source)
    sys.argv = argv
    exec(python_code, {"__name__": "__main__"})

def repl():
    print(f"HinglishPy {VERSION} - Apna Compiler, Poora Hinglish Me")
    print("Bahar nikalne ke liye: bahar")
    print("")
    my_vars = {}
    while True:
        try:
            line = input("hinglishpy >>> ")
        except (EOFError, KeyboardInterrupt):
            print("\nAlvida!")
            break
        if line.strip() in ["bahar", "exit", "quit"]:
            print("Alvida!")
            break
        if line.strip() == "":
            continue
        full_code = line
        if line.strip().endswith(":"):
            print("... block chal raha hai, khatam karne ke liye khali Enter")
            while True:
                try:
                    nxt = input("... ")
                except Exception:
                    break
                if nxt.strip() == "":
                    break
                full_code += "\n" + nxt
        try:
            python_code = compile_code(full_code)
            exec(python_code, my_vars)
        except SystemExit:
            continue
        except Exception as e:
            print(f"Galti / Error: {e}")

def main():
    args = sys.argv[1:]
    if not args:
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
        run_source(args[1], ["-c"] + args[2:])
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
    run_source(source, [script] + args[1:])

if __name__ == "__main__":
    main()
