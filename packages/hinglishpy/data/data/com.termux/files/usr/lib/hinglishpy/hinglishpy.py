# HinglishPy REPL
import sys
from compiler import compile_code

def main():
    if len(sys.argv) > 1:
        sys.argv = ["compiler.py", sys.argv[1], "run"]
        from compiler import main as comp_main
        comp_main()
        return
    print("HinglishPy 3.0 - Apna Compiler, Poora Hinglish Me")
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
                except:
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

if __name__ == "__main__":
    main()
