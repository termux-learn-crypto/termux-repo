"""HinglishPy .hl files ka import hook."""
import importlib.abc
import importlib.util
import os
import sys


class HinglishHLLoader(importlib.abc.Loader):
    def __init__(self, path):
        self.path = path

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.path, "r", encoding="utf-8") as f:
            source = f.read()
        from apna import compile_source
        from apna.runtime import run_with_hinglish_errors
        code = compile_source(source)
        run_with_hinglish_errors(code, module.__dict__, {"filename": self.path})


_HSTL_DIR = os.path.dirname(os.path.abspath(__file__)) + "/../"


class HinglishHLFinder(importlib.abc.MetaPathFinder):
    def __init__(self):
        self._path_dirs = []

    def add_path(self, path):
        if path and path not in self._path_dirs:
            self._path_dirs.append(path)

    def find_spec(self, fullname, path=None, target=None):
        parts = fullname.split(".")
        name = parts[-1]
        # hstl module (installed as top-level import)
        if name == "hstl":
            try:
                return importlib.util.find_spec("hstl")
            except Exception:
                return None
        for d in self._path_dirs:
            candidate = os.path.join(d, name + ".hl")
            if os.path.isfile(candidate):
                return importlib.util.spec_from_file_location(
                    fullname, candidate, loader=HinglishHLLoader(candidate)
                )
        return None


_finder = HinglishHLFinder()
sys.meta_path.insert(0, _finder)


def add_script_dir(script_path):
    d = os.path.dirname(os.path.abspath(script_path))
    _finder.add_path(d)
    if d not in sys.path:
        sys.path.insert(0, d)
