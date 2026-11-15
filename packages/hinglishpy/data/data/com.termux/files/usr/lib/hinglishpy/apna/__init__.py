from .lexer import tokenize
from .parser import Parser
from .codegen import generate
from .errors import HinglishError


def compile_source(source):
    tokens = tokenize(source)
    module = Parser(tokens).parse()
    return generate(module)
