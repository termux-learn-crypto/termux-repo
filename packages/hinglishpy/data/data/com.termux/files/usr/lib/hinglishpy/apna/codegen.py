from . import nodes as N

NAME_MAP = {
    "lambai": "len", "ginti": "range", "kramank": "enumerate",
    "shabdkosh": "dict", "suchi": "list", "samuh": "set", "yugm": "tuple",
    "shabd": "str", "sankhya": "int", "dashmalav": "float", "mishrit": "complex",
    "tarkik": "bool", "pariman": "abs", "nyuntam": "min", "adhiktam": "max",
    "yog": "sum", "krambadh": "sorted", "ulta": "reversed",
    "ank": "ord", "akshar": "chr", "gol": "round", "ghat": "pow",
    "naksha": "map", "chhalni": "filter", "jodna": "zip",
    "kholo": "open", "prakar": "type", "pehchan": "id",
    "bahar": "exit", "puchho": "input", "khud": "self",
}

PREC = {
    "ConditionalExp": 1, "Lambda": 1, "BoolOp": 2, "BinOp:or": 2,
    "UnaryOp:not": 3, "Compare": 4, "BinOp:|": 5, "BinOp:^": 6, "BinOp:&": 7,
    "BinOp:<<": 8, "BinOp:>>": 8, "BinOp:+": 9, "BinOp:-": 9,
    "BinOp:*": 10, "BinOp:/": 10, "BinOp://": 10, "BinOp:%": 10, "BinOp:@": 10,
    "UnaryOp:+": 11, "UnaryOp:-": 11, "UnaryOp:~": 11,
    "BinOp:**": 12, "Await": 11,
}

class Codegen:
    def __init__(self):
        self.lines = []
        self.indent = 0

    def emit(self, line=""):
        if line:
            self.lines.append("    " * self.indent + line)
        else:
            self.lines.append("")

    def result(self):
        return "\n".join(self.lines) + ("\n" if self.lines else "")

    def prec(self, node):
        if isinstance(node, N.NamedExpr):
            return 1
        if isinstance(node, N.BoolOp):
            return 3 if node.op == "and" else 2
        if isinstance(node, N.ConditionalExp):
            return 1
        if isinstance(node, N.Lambda):
            return 1
        if isinstance(node, N.Compare):
            return 4
        if isinstance(node, N.UnaryOp):
            return 3 if node.op == "not" else 11
        if isinstance(node, N.Await):
            return 11
        if isinstance(node, N.BinOp):
            return {
                "|": 5, "^": 6, "&": 7, "<<": 8, ">>": 8,
                "+": 9, "-": 9, "*": 10, "/": 10, "//": 10, "%": 10, "@": 10, "**": 12,
            }.get(node.op, 9)
        return 20

    def walk_expr(self, node, parent_prec=0):
        s = self.expr(node)
        if self.prec(node) < parent_prec:
            return f"({s})"
        return s

    def expr(self, node):
        if isinstance(node, N.Name):
            return NAME_MAP.get(node.id, node.id)
        if isinstance(node, N.Constant):
            raw = str(node.value)
            if re.match(r"(?i)^(fr|rb|br|rf|f|r|b)?[\'\"]", raw):
                return _transform_fstring(raw)
            return raw
        if isinstance(node, N.Attribute):
            return f"{self.walk_expr(node.value, 19)}.{node.attr}"
        if isinstance(node, N.Subscript):
            return f"{self.walk_expr(node.value, 19)}[{self.expr(node.slice)}]"
        if isinstance(node, N.Slice):
            parts = [
                self.expr(node.lower) if node.lower is not None else "",
                self.expr(node.upper) if node.upper is not None else "",
                self.expr(node.step) if node.step is not None else "",
            ]
            while len(parts) > 2 and parts[-1] == "":
                parts.pop()
            return ":".join(parts)
        if isinstance(node, N.Starred):
            return f"*{self.expr(node.value)}"
        if isinstance(node, N.List):
            return "[" + ", ".join(self.expr(e) for e in node.elts) + "]"
        if isinstance(node, N.Tuple):
            if len(node.elts) == 1:
                return "(" + self.expr(node.elts[0]) + ",)"
            return "(" + ", ".join(self.expr(e) for e in node.elts) + ")"
        if isinstance(node, N.Set):
            return "{" + ", ".join(self.expr(e) for e in node.elts) + "}"
        if isinstance(node, N.Dict):
            items = []
            for k, v in zip(node.keys, node.values):
                if k is None:
                    items.append(f"**{self.expr(v)}")
                else:
                    items.append(f"{self.expr(k)}: {self.expr(v)}")
            return "{" + ", ".join(items) + "}"
        if isinstance(node, N.ListComp):
            return f"[{self.expr(node.elt)} {self.comprehension(node.generators)}]"
        if isinstance(node, N.SetComp):
            return f"{{{self.expr(node.elt)} {self.comprehension(node.generators)}}}"
        if isinstance(node, N.DictComp):
            return f"{{{self.expr(node.key)}: {self.expr(node.value)} {self.comprehension(node.generators)}}}"
        if isinstance(node, N.GeneratorExp):
            return f"({self.expr(node.elt)} {self.comprehension(node.generators)})"
        if isinstance(node, N.Lambda):
            params = self.params(node.params)
            return f"lambda {params}: {self.expr(node.body)}"
        if isinstance(node, N.Await):
            return f"await {self.walk_expr(node.value, 11)}"
        if isinstance(node, N.Yield):
            if node.value is None:
                return "yield"
            return f"yield {self.expr(node.value)}"
        if isinstance(node, N.YieldFrom):
            return f"yield from {self.expr(node.value)}"
        if isinstance(node, N.NamedExpr):
            return f"{node.target.id} := {self.expr(node.value)}"
        if isinstance(node, N.BoolOp):
            is_and = node.op == "and"
            op = " and " if is_and else " or "
            p = 3 if is_and else 2
            parts = [self.walk_expr(v, p) for v in node.values]
            return op.join(parts)
        if isinstance(node, N.UnaryOp):
            if node.op == "not":
                return f"not {self.walk_expr(node.operand, 3)}"
            return f"{node.op}{self.walk_expr(node.operand, 11)}"
        if isinstance(node, N.BinOp):
            p = self.prec(node)
            right_prec = p if node.op == "**" else p + 1
            return f"{self.walk_expr(node.left, p + 1)} {node.op} {self.walk_expr(node.right, right_prec)}"
        if isinstance(node, N.Compare):
            parts = [self.walk_expr(node.left, 4)]
            for op, comp in zip(node.ops, node.comparators):
                parts.append(op)
                parts.append(self.walk_expr(comp, 4))
            return " ".join(parts)
        if isinstance(node, N.ConditionalExp):
            return (f"{self.walk_expr(node.body, 1)} if {self.expr(node.test)} "
                    f"else {self.walk_expr(node.orelse, 1)}")
        if isinstance(node, N.Call):
            args = [self.expr(a) for a in node.args]
            for kw in node.keywords:
                if kw.arg is None:
                    args.append(f"**{self.expr(kw.value)}")
                else:
                    args.append(f"{kw.arg}={self.expr(kw.value)}")
            return f"{self.walk_expr(node.func, 19)}({', '.join(args)})"
        raise TypeError(f"Unknown expression node: {node!r}")

    def comprehension(self, generators):
        parts = []
        for gen in generators:
            target = self.expr(gen.target)
            prefix = "async for" if gen.is_async else "for"
            iter_expr = self.expr(gen.iter)
            ifs = "".join(f" if {self.expr(i)}" for i in gen.ifs)
            parts.append(f"{prefix} {target} in {iter_expr}{ifs}")
        return " ".join(parts)

    def statement(self, node, indent=0):
        self.indent = indent
        method = getattr(self, "stmt_" + type(node).__name__, None)
        if method is None:
            raise TypeError(f"Unknown statement node: {node!r}")
        method(node)
        self.indent = indent

    def body(self, stmts, indent):
        for s in stmts:
            self.statement(s, indent)
        self.indent = indent - 1

    # ---------- statements ----------

    def stmt_TypeAlias(self, node):
        self.emit(f"type {node.name} = {self.expr(node.value)}")

    def stmt_Module(self, node):
        self.body(node.body, 0)

    def _target(self, node):
        if isinstance(node, N.Tuple):
            return ", ".join(self.expr(e) for e in node.elts)
        return self.expr(node)

    def stmt_Assign(self, node):
        targets = []
        for i, t in enumerate(node.targets):
            if isinstance(t, N.Tuple) and len(node.targets) == 1:
                targets.append(", ".join(self.expr(e) for e in t.elts))
            else:
                targets.append(self._target(t))
        self.emit(" = ".join(targets) + f" = {self.expr(node.value)}")

    def stmt_AugAssign(self, node):
        self.emit(f"{self._target(node.target)} {node.op} {self.expr(node.value)}")

    def stmt_AnnAssign(self, node):
        t = self._target(node.target)
        ann = self.expr(node.annotation)
        if node.value is not None:
            self.emit(f"{t}: {ann} = {self.expr(node.value)}")
        else:
            self.emit(f"{t}: {ann}")

    def stmt_ExprStmt(self, node):
        self.emit(self.expr(node.value))

    def stmt_If(self, node):
        self.emit(f"if {self.expr(node.test)}:")
        level = self.indent
        self.body(node.body, self.indent + 1)
        self.indent = level
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], N.If):
                elif_node = node.orelse[0]
                self.emit(f"elif {self.expr(elif_node.test)}:")
                self.body(elif_node.body, self.indent + 1)
                self.indent = level
                rest = elif_node.orelse
                while len(rest) == 1 and isinstance(rest[0], N.If):
                    elif_node = rest[0]
                    self.emit(f"elif {self.expr(elif_node.test)}:")
                    self.body(elif_node.body, self.indent + 1)
                    self.indent = level
                    rest = elif_node.orelse
                if rest:
                    self.emit("else:")
                    self.body(rest, self.indent + 1)
            else:
                self.emit("else:")
                self.body(node.orelse, self.indent + 1)

    def stmt_While(self, node):
        self.emit(f"while {self.expr(node.test)}:")
        self.body(node.body, self.indent + 1)
        if node.orelse:
            self.emit("else:")
            self.body(node.orelse, self.indent + 1)

    def stmt_For(self, node):
        prefix = "async for" if node.is_async else "for"
        target = self._target(node.target)
        self.emit(f"{prefix} {target} in {self.expr(node.iter)}:")
        self.body(node.body, self.indent + 1)
        if node.orelse:
            self.emit("else:")
            self.body(node.orelse, self.indent + 1)

    def stmt_With(self, node):
        prefix = "async with" if node.is_async else "with"
        items = []
        for item in node.items:
            expr = self.expr(item.context_expr)
            if item.optional_vars is not None:
                items.append(f"{expr} as {self._target(item.optional_vars)}")
            else:
                items.append(expr)
        self.emit(f"{prefix} {', '.join(items)}:")
        self.body(node.body, self.indent + 1)

    def params(self, params):
        parts = []
        def pname(n):
            return "self" if n == "khud" else n

        for p in params:
            if p.kind == "staronly":
                parts.append("*")
                continue
            if p.kind == "slash":
                parts.append("/")
                continue
            text = ("*" if p.kind == "vararg" else "**" if p.kind == "kwarg" else "") + pname(p.name)
            if p.annotation is not None:
                text += f": {self.expr(p.annotation)}"
            if p.default is not None:
                text += f"={self.expr(p.default)}"
            parts.append(text)
        return ", ".join(parts)

    def stmt_FunctionDef(self, node):
        for dec in node.decorators:
            self.emit(f"@{self.expr(dec)}")
        prefix = "async def" if node.is_async else "def"
        returns = f" -> {self.expr(node.returns)}" if node.returns is not None else ""
        self.emit(f"{prefix} {node.name}({self.params(node.params)}){returns}:")
        self.body(node.body, self.indent + 1)

    def stmt_ClassDef(self, node):
        for dec in node.decorators:
            self.emit(f"@{self.expr(dec)}")
        bases = [self.expr(b) for b in node.bases]
        for kw in node.keywords:
            bases.append(f"{kw.arg}={self.expr(kw.value)}")
        suffix = f"({', '.join(bases)})" if bases else ""
        self.emit(f"class {node.name}{suffix}:")
        self.body(node.body, self.indent + 1)

    def stmt_Return(self, node):
        if node.value is None:
            self.emit("return")
        else:
            self.emit(f"return {self.expr(node.value)}")

    def stmt_Yield(self, node):
        self.emit(self.expr(N.Yield(value=node.value)))

    def stmt_Raise(self, node):
        if node.exc is None:
            self.emit("raise")
            return
        text = f"raise {self.expr(node.exc)}"
        if node.cause is not None:
            text += f" from {self.expr(node.cause)}"
        self.emit(text)

    def stmt_Assert(self, node):
        text = f"assert {self.expr(node.test)}"
        if node.msg is not None:
            text += f", {self.expr(node.msg)}"
        self.emit(text)

    def stmt_Break(self, node):
        self.emit("break")

    def stmt_Continue(self, node):
        self.emit("continue")

    def stmt_Pass(self, node):
        self.emit("pass")

    def stmt_Delete(self, node):
        self.emit(f"del {', '.join(self._target(t) for t in node.targets)}")

    def stmt_Global(self, node):
        self.emit(f"global {', '.join(node.names)}")

    def stmt_Nonlocal(self, node):
        self.emit(f"nonlocal {', '.join(node.names)}")

    def stmt_Import(self, node):
        parts = []
        for alias in node.names:
            text = alias.name
            if alias.asname:
                text += f" as {alias.asname}"
            parts.append(text)
        self.emit(f"import {', '.join(parts)}")

    def stmt_ImportFrom(self, node):
        names = []
        for alias in node.names:
            text = alias.name
            if alias.asname:
                text += f" as {alias.asname}"
            names.append(text)
        dots = "." * node.level
        module = dots + (node.module or "")
        if module.startswith(".") and node.module:
            module = dots + node.module
        self.emit(f"from {module} import {', '.join(names)}")

    def stmt_Try(self, node):
        self.emit("try:")
        self.body(node.body, self.indent + 1)
        for handler in node.handlers:
            prefix = "except* " if handler.star else "except "
            if handler.type is None:
                self.emit(("except*:" if handler.star else "except:"))
            else:
                exc = self.expr(handler.type)
                if handler.name:
                    self.emit(f"{prefix}{exc} as {handler.name}:")
                else:
                    self.emit(f"{prefix}{exc}:")
            self.body(handler.body, self.indent + 1)
        if node.orelse:
            self.emit("else:")
            self.body(node.orelse, self.indent + 1)
        if node.finalbody:
            self.emit("finally:")
            self.body(node.finalbody, self.indent + 1)


    # ---------- match / case ----------

    def stmt_Match(self, node):
        level = self.indent
        self.emit(f"match {self.expr(node.subject)}:")
        for case in node.cases:
            guard = f" if {self.expr(case.guard)}" if case.guard is not None else ""
            self.indent = level + 1
            self.emit(f"case {self.pattern(case.pattern, top=True)}{guard}:")
            self.body(case.body, level + 2)
            self.indent = level + 1

    def pattern(self, node, top=False, parens=False):
        def bind(name):
            return NAME_MAP.get(name, name)

        if isinstance(node, N.LiteralPattern):
            return str(node.value)
        if isinstance(node, N.CapturePattern):
            return bind(node.name)
        if isinstance(node, N.WildcardPattern):
            return "_"
        if isinstance(node, N.ValuePattern):
            return node.dotted
        if isinstance(node, N.SequencePattern):
            close = "[" if node.bracket == "[" else "("
            parts = [self.pattern(e) for e in node.elts]
            return f"{close}{', '.join(parts)}" + ("]" if node.bracket == "[" else ")")
        if isinstance(node, N.StarPattern):
            return f"*{bind(node.name)}"
        if isinstance(node, N.MappingPattern):
            parts = []
            for pair in node.pairs:
                parts.append(f"{self.pattern(pair.key)}: {self.pattern(pair.pattern)}")
            if node.rest is not None:
                parts.append(f"**{bind(node.rest)}")
            return "{" + ", ".join(parts) + "}"
        if isinstance(node, N.ClassPattern):
            args = [self.pattern(a) for a in node.args]
            for kw in node.kwargs:
                args.append(f"{kw.name}={self.pattern(kw.pattern)}")
            return f"{node.dotted}({', '.join(args)})"
        if isinstance(node, N.AsPattern):
            left = self.pattern(node.pattern)
            return f"{left} as {bind(node.name)}"
        if isinstance(node, N.OrPattern):
            joined = " | ".join(self.pattern(v) for v in node.values)
            if top:
                return joined
            return f"({joined})"
        raise TypeError(f"Unknown pattern node: {node!r}")


def generate(module):
    cg = Codegen()
    cg.statement(module)
    return cg.result()


import re

_FSTRING_RE = re.compile(r"(?i)^(fr|rb|br|rf|f|r|b)?(\"\"\"|'''|\"|')")

def _split_field(field):
    depth = 0
    in_str = None
    for i, ch in enumerate(field):
        if in_str:
            if ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'"):
            in_str = ch
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == ':' and depth == 0:
            return field[:i], field[i + 1:]
    return field, None

def _split_debug(text):
    depth = 0
    in_str = None
    for i, ch in enumerate(text):
        if in_str:
            if ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'"):
            in_str = ch
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "=" and depth == 0:
            return text[:i], text[i + 1:]
    return text, None

def _compile_ffield(field):
    text = field.strip()
    m = re.match(r"^(.*)!([rsa])$", text, re.S)
    conversion = ""
    if m:
        text = m.group(1)
        conversion = "!" + m.group(2)
    debug_expr, debug_rest = _split_debug(text)
    if debug_rest is not None:
        spec = debug_rest
        if spec.startswith(":"):
            spec = spec[1:]
        if spec == "":
            spec = None
        expr_part = debug_expr
        is_debug = True
    else:
        expr_part, spec = _split_field(text)
        is_debug = False
    expr_code = _compile_fragment(expr_part.strip())
    if expr_code is None:
        return field
    result = "{" + expr_code
    if is_debug:
        result += "="
    result += conversion
    if spec is not None:
        spec = _transform_fstring_body(spec)
        result += ":" + spec
    return result + "}"

def _compile_fragment(src):
    from .lexer import tokenize
    from .parser import Parser
    try:
        tokens = tokenize(src)
        module = Parser(tokens).parse()
        return generate(module).rstrip("\n").strip()
    except Exception:
        return None

def _transform_fstring_body(body):
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == '\\':
            out.append(body[i:i + 2])
            i += 2
            continue
        if body.startswith('{{', i):
            out.append('{{')
            i += 2
            continue
        if body.startswith('}}', i):
            out.append('}}')
            i += 2
            continue
        if ch == '{':
            depth = 1
            j = i + 1
            while j < len(body) and depth:
                c = body[j]
                if c == '\\':
                    j += 2
                    continue
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                j += 1
            out.append(_compile_ffield(body[i + 1:j - 1]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)

def _transform_fstring(raw):
    m = _FSTRING_RE.match(raw)
    prefix = (m.group(1) or "").lower()
    quote = m.group(2)
    if "f" not in prefix:
        return raw
    body = raw[m.end():-len(quote)]
    return prefix + quote + _transform_fstring_body(body) + quote