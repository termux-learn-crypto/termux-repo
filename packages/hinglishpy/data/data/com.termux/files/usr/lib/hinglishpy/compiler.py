import sys
import os

from apna import compile_source
from apna.errors import HinglishError

def show_error(line_no, line, msg_hinglish, msg_english, suggestion=None):
    print(f"\n[ HinglishPy Galti / Error ]")
    if line_no:
        if line:
            print(f"Line {line_no}: {line}")
        else:
            print(f"Line {line_no}")
    print(f"Hinglish: {msg_hinglish}")
    print(f"English: {msg_english}")
    if suggestion:
        print(f"Sujhav / Suggestion: {suggestion}")
    print()
    sys.exit(1)

def compile_code(code):
    try:
        return compile_source(code)
    except HinglishError as e:
        show_error(e.line, None, e.msg_hinglish, e.msg_english)

def main():
    if len(sys.argv) < 2:
        print("HinglishPy ka use:")
        print("  python compiler.py test.hl run")
        return
    input_file = sys.argv[1]
    if not input_file.endswith(".hl"):
        show_error(0, input_file, "File .hl honi chahiye", "File must end with .hl")
    if not os.path.exists(input_file):
        print(f"Galti / Error: File nahi mili - {input_file}")
        return
    with open(input_file, "r", encoding="utf-8") as f:
        hinglish_code = f.read()
    python_code = compile_code(hinglish_code)
    output_file = input_file.replace(".hl", ".py")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Compiled by HinglishPy\n")
        f.write(python_code)
    print(f"Ho gaya! {input_file} -> {output_file} ban gaya")
    if len(sys.argv) > 2 and sys.argv[2] == "run":
        print("--- Chal raha hai / Running ---\n")
        exec(python_code, {"__name__": "__main__"})

if __name__ == "__main__":
    main()
