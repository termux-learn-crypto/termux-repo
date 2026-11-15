from .lexer import Token, tokenize
from .errors import HinglishError
from . import nodes as N

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        i = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[i]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def accept(self, *types):
        if self.current().type in types:
            return self.advance()
        return None

    def expect(self, type_, msg_hinglish, msg_english=None):
        tok = self.current()
        if tok.type == type_:
            return self.advance()
        got = tok.type if tok.type not in ("NAME", "STRING", "NUMBER") else repr(tok.value)
        raise HinglishError(tok.line,
                            f"{msg_hinglish} (mile: {got})",
                            f"{msg_english or msg_hinglish} (got: {got})")

    def at_end(self):
        return self.current().type == "EOF"

    def skip_newlines(self):
        while self.current().type == "NEWLINE":
            self.advance()

    def parse(self):
        body = []
        self.skip_newlines()
        while not self.at_end():
            body.append(self.parse_statement())
            self.skip_newlines()
        return N.Module(body=body)

    def parse_block(self):
        self.expect(":", "Line ke aakhir me ':' chahiye", "Expected ':' at end of statement")
        self.skip_newlines()
        self.expect("INDENT", "Andar wali lines ko indent karo", "Expected indented block")
        self.skip_newlines()
        body = []
        while not self.at_end() and self.current().type != "DEDENT":
            body.append(self.parse_statement())
            self.skip_newlines()
        if not body:
            raise HinglishError(self.current().line,
                                "Block khali hai",
                                "Empty block")
        self.expect("DEDENT", "Indent sahi band nahi hui", "Expected dedent")
        return body

    # ---------- statements ----------

    def parse_statement(self):
        tok = self.current()
        line = tok.line

        if tok.type == "@":
            decorators = []
            while self.accept("@"):
                decorators.append(self.parse_expression())
                self.expect("NEWLINE", "Decorator ke baad newline chahiye", "Expected newline after decorator")
                self.skip_newlines()
            stmt = self.parse_statement()
            if isinstance(stmt, (N.FunctionDef, N.ClassDef)):
                stmt.decorators = decorators + list(stmt.decorators)
                return stmt
            raise HinglishError(tok.line, "Decorator sirf kaam/varg ke upar", "Decorators only on functions/classes")

        if tok.type == "ASYNC":
            self.advance()
            nxt = self.current()
            if nxt.type == "DEF":
                return self.parse_function(is_async=True)
            if nxt.type in ("FOR", "WITH"):
                return self.parse_for_or_with(is_async=True)
            raise HinglishError(tok.line, "asink ke baad kaam/har/saath chahiye", "Expected kaam/har/saath after asink")

        if tok.type == "DEF":
            return self.parse_function(is_async=False)
        if tok.type == "CLASS":
            return self.parse_class(decorators=[])
        if tok.type == "IF":
            return self.parse_if()
        if tok.type == "ELIF":
            raise HinglishError(tok.line, "nahito bina agar ke nahi aata", "nahito without agar")
        if tok.type == "ELSE":
            raise HinglishError(tok.line, "warna bina agar/jabtak/har/koshish ke nahi aata", "warna without agar/jabtak/har/koshish")
        if tok.type == "WHILE":
            return self.parse_while()
        if tok.type in ("FOR", "WITH"):
            return self.parse_for_or_with(is_async=False)
        if tok.type == "MATCH":
            return self.parse_match()
        if tok.type == "CASE":
            raise HinglishError(tok.line, "case bina match ke nahi aata", "case without match")
        if tok.type == "TRY":
            return self.parse_try()
        if tok.type == "RETURN":
            self.advance()
            value = None if self.current().type == "NEWLINE" else self.parse_expression_list()
            self.expect("NEWLINE", "Line yahan khatam karni thi", "Expected end of line")
            return N.Return(value=value)
        if tok.type == "YIELD":
            self.advance()
            value = None if self.current().type == "NEWLINE" else self.parse_expression_list()
            self.expect("NEWLINE", "Line yahan khatam karni thi", "Expected end of line")
            return N.ExprStmt(value=N.Yield(value=value))
        if tok.type == "BREAK":
            self.advance(); self.expect("NEWLINE", "Line khatam karo", "Expected end of line"); return N.Break()
        if tok.type == "CONTINUE":
            self.advance(); self.expect("NEWLINE", "Line khatam karo", "Expected end of line"); return N.Continue()
        if tok.type == "PASS":
            self.advance(); self.expect("NEWLINE", "Line khatam karo", "Expected end of line"); return N.Pass()
        if tok.type == "ASSERT":
            self.advance()
            test = self.parse_expression()
            msg = None
            if self.accept(","):
                msg = self.parse_expression()
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            return N.Assert(test=test, msg=msg)
        if tok.type == "RAISE":
            self.advance()
            exc = None
            if self.current().type != "NEWLINE":
                exc = self.parse_expression()
                if self.accept("FROM") or self.current().type == "FROM":
                    cause = self.parse_expression()
                    self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
                    return N.Raise(exc=exc, cause=cause)
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            return N.Raise(exc=exc, cause=None)
        if tok.type == "DEL":
            self.advance()
            targets = self.parse_target_list()
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            return N.Delete(targets=targets)
        if tok.type in ("GLOBAL", "NONLOCAL"):
            self.advance()
            names = [self.expect("NAME", "Naam chahiye", "Expected name").value]
            while self.accept(","):
                names.append(self.expect("NAME", "Naam chahiye", "Expected name").value)
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            return N.Global(names=names) if tok.type == "GLOBAL" else N.Nonlocal(names=names)
        if tok.type == "IMPORT":
            return self.parse_import()
        if tok.type == "FROM":
            return self.parse_from_import()
        if tok.type == "PRINT":
            self.advance()
            if self.accept("("):
                args, keywords = self.parse_call_args()
            else:
                args, keywords = self.parse_comma_args({"NEWLINE"})
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            return N.ExprStmt(value=N.Call(func=N.Name(id="print"), args=args, keywords=keywords))
        if tok.type == "DEDENT":
            raise HinglishError(tok.line, "Sahi line nahi hui", "Unexpected dedent")

        return self.parse_expr_or_assign()

    _AUGOPS = ("+=", "-=", "*=", "/=", "//=", "%=", "**=", "@=", "&=", "|=", "^=", ">>=", "<<=")

    def _parse_assign_units(self):
        elts = [self._parse_star_one()]
        while self.accept(","):
            if self.current().type in ("=", "NEWLINE"):
                break
            elts.append(self._parse_star_one())
        return elts

    def _make_target(self, elts):
        if len(elts) == 1:
            return elts[0]
        return N.Tuple(elts=elts)

    def parse_expr_or_assign(self):
        first = self._parse_star_one()
        tok = self.current()
        if tok.type in self._AUGOPS:
            self.advance()
            if isinstance(first, (N.Tuple, N.List, N.Starred)):
                raise HinglishError(tok.line,
                                    "augmented assignment ka target simple hona chahiye",
                                    "Augmented assignment needs a simple target")
            value = self.parse_expression_list()
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            self._check_assignable(first)
            return N.AugAssign(target=first, op=tok.type, value=value)
        if tok.type in (",", "="):
            elts = [first]
            trailing_comma = False
            while self.accept(","):
                trailing_comma = True
                if self.current().type in ("=", "NEWLINE"):
                    break
                elts.append(self._parse_star_one())
                trailing_comma = False
            if self.current().type == "=":
                segments = [elts]
                while self.accept("="):
                    save = self.pos
                    units = None if self.current().type == "LAMBDA" else self._parse_assign_units()
                    if units is not None and self.current().type == "=":
                        segments.append(units)
                    else:
                        self.pos = save
                        value = self.parse_expression_list()
                        self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
                        targets = [self._make_target(seg) for seg in segments]
                        for st in targets:
                            self._check_assignable(st)
                        return N.Assign(targets=targets, value=value)
                raise HinglishError(self.current().line,
                                    "assignment adhoora hai",
                                    "Incomplete assignment")
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            if len(elts) == 1 and trailing_comma:
                return N.ExprStmt(value=N.Tuple(elts=elts))
            if len(elts) == 1:
                return N.ExprStmt(value=elts[0])
            return N.ExprStmt(value=N.Tuple(elts=elts))
        if self.accept(":"):
            annotation = self.parse_expression()
            value = None
            if self.accept("="):
                value = self.parse_expression()
            self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
            return N.AnnAssign(target=first, annotation=annotation, value=value)
        self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
        return N.ExprStmt(value=first)

    def _check_assignable(self, node):
        if isinstance(node, (N.Name, N.Tuple, N.List, N.Subscript, N.Attribute, N.Starred)):
            if isinstance(node, (N.Tuple, N.List)):
                for e in node.elts:
                    self._check_assignable(e)
            if isinstance(node, N.Starred):
                self._check_assignable(node.value)
            return
        if isinstance(node, N.Constant):
            raise HinglishError(self.current().line,
                                "Ye value assignment nahi ho sakti",
                                "Cannot assign to a literal")
        raise HinglishError(self.current().line,
                            "Ye target assignment ke liye sahi nahi",
                            "Invalid assignment target")

    def parse_expression_list(self):
        exprs = [self.parse_expression()]
        trailing = False
        while self.accept(","):
            trailing = True
            if self.current().type in ("NEWLINE", ")", "]", "}"):
                break
            exprs.append(self.parse_expression())
            trailing = False
        if len(exprs) == 1 and not trailing:
            return exprs[0]
        return N.Tuple(elts=exprs)

    def parse_target_list(self):
        targets = [self.parse_expression()]
        while self.accept(","):
            if self.current().type == "NEWLINE":
                break
            targets.append(self.parse_expression())
        return targets

    def parse_if(self):
        self.advance()
        test = self.parse_expression()
        body = self.parse_block()
        node = N.If(test=test, body=body, orelse=[])
        current = node
        while self.current().type == "ELIF":
            self.advance()
            elif_test = self.parse_expression()
            elif_body = self.parse_block()
            elif_node = N.If(test=elif_test, body=elif_body, orelse=[])
            current.orelse = [elif_node]
            current = elif_node
        if self.current().type == "ELSE":
            self.advance()
            current.orelse = self.parse_block()
        return node


    def parse_while(self):
        self.advance()
        test = self.parse_expression()
        body = self.parse_block()
        orelse = []
        if self.current().type == "ELSE":
            self.advance()
            orelse = self.parse_block()
        return N.While(test=test, body=body, orelse=orelse)

    def parse_for_or_with(self, is_async):
        tok = self.current()
        if tok.type == "FOR":
            self.advance()
            target = self.parse_star_target()
            self.expect("IN", "har ke baad 'me' chahiye", "Expected 'me' after target")
            iter_ = self.parse_expression()
            body = self.parse_block()
            orelse = []
            if self.current().type == "ELSE":
                self.advance()
                orelse = self.parse_block()
            return N.For(target=target, iter=iter_, body=body, orelse=orelse, is_async=is_async)
        self.advance()
        items = []
        while True:
            item_expr = self.parse_expression()
            as_var = None
            if self.accept("AS"):
                as_var = self.parse_expression()
            items.append(N.WithItem(context_expr=item_expr, optional_vars=as_var))
            if not self.accept(","):
                break
        body = self.parse_block()
        return N.With(items=items, body=body, is_async=is_async)

    def parse_try(self):
        self.advance()
        body = self.parse_block()
        handlers = []
        while self.current().type == "EXCEPT":
            self.advance()
            exc_type = None
            name = None
            if self.current().type != ":":
                exc_type = self.parse_expression()
                if self.accept("AS"):
                    name = self.expect("NAME", "Naam chahiye 'as' ke baad", "Expected name after as").value
            handler_body = self.parse_block()
            handlers.append(N.ExceptHandler(type=exc_type, name=name, body=handler_body))
        orelse = []
        if self.current().type == "ELSE":
            self.advance()
            orelse = self.parse_block()
        finalbody = []
        if self.current().type == "FINALLY":
            self.advance()
            finalbody = self.parse_block()
        if not handlers and not finalbody:
            raise HinglishError(self.current().line,
                                "koshish ke baad pakdo ya ant chahiye",
                                "try needs except or finally")
        return N.Try(body=body, handlers=handlers, orelse=orelse, finalbody=finalbody)

    def parse_dotted_name(self):
        name = self.expect("NAME", "Naam chahiye", "Expected name").value
        while self.accept("."):
            name += "." + self.expect("NAME", "Naam chahiye '.' ke baad", "Expected name after '.'").value
        return name

    def parse_import(self):
        self.advance()
        names = []
        while True:
            dotted = self.parse_dotted_name()
            asname = None
            if self.accept("AS"):
                asname = self.expect("NAME", "Naam chahiye 'jaise' ke baad", "Expected name after jaise").value
            names.append(N.Alias(name=dotted, asname=asname))
            if not self.accept(","):
                break
        self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
        return N.Import(names=names)

    def parse_from_import(self):
        self.advance()
        level = 0
        while self.accept("."):
            level += 1
        module = ""
        if self.current().type != "IMPORT":
            module = self.parse_dotted_name()
        self.expect("IMPORT", "'lao' chahiye 'se X' ke baad", "Expected 'lao' after 'se X'")
        names = []
        if self.accept("*"):
            names.append(N.Alias(name="*", asname=None))
        else:
            while True:
                name = self.expect("NAME", "Naam chahiye", "Expected name").value
                asname = None
                if self.accept("AS"):
                    asname = self.expect("NAME", "Naam chahiye 'jaise' ke baad", "Expected name after jaise").value
                names.append(N.Alias(name=name, asname=asname))
                if not self.accept(","):
                    break
        self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
        return N.ImportFrom(module=module, names=names, level=level)

    def parse_params(self):
        params = []
        seen_star = False
        self.expect("(", "'(' chahiye", "Expected '('")
        if self.accept(")"):
            return params
        while True:
            kind = "pos"
            if self.accept("**"):
                name_tok = self.expect("NAME", "Naam chahiye '**' ke baad", "Expected name after '**'")
                params.append(N.Param(name=name_tok.value, default=None, annotation=None, kind="kwarg"))
                if not self.accept(","):
                    break
                continue
            if self.accept("*"):
                if self.current().type == "NAME":
                    name_tok = self.advance()
                    params.append(N.Param(name=name_tok.value, default=None, annotation=None, kind="vararg"))
                    seen_star = True
                else:
                    params.append(N.Param(name="", default=None, annotation=None, kind="staronly"))
                    seen_star = True
                if not self.accept(","):
                    break
                continue
            if self.accept("/"):
                params.append(N.Param(name="", default=None, annotation=None, kind="slash"))
                if not self.accept(","):
                    break
                continue
            name_tok = self.expect("NAME", "Parameter ka naam chahiye", "Expected parameter name")
            annotation = None
            if self.accept(":"):
                annotation = self.parse_expression()
            default = None
            if self.accept("="):
                default = self.parse_expression()
            kind = "pos" if not seen_star else "kwonly"
            params.append(N.Param(name=name_tok.value, default=default, annotation=annotation, kind=kind))
            if not self.accept(","):
                break
        self.expect(")", "')' chahiye", "Expected ')'")
        return params

    def parse_function(self, is_async=False, decorators=None):
        self.advance()
        name_tok = self.expect("NAME", "kaam ke baad function ka naam chahiye", "Expected function name after 'kaam'")
        params = self.parse_params()
        returns = None
        if self.accept("->"):
            returns = self.parse_expression()
        body = self.parse_block()
        if not body:
            raise HinglishError(name_tok.line, "Function khali nahi ho sakta", "Function body is empty")
        return N.FunctionDef(name=name_tok.value, params=params, body=body,
                             decorators=list(decorators or []), returns=returns, is_async=is_async)

    def parse_class(self, decorators=None):
        self.advance()
        name_tok = self.expect("NAME", "varg ke baad class ka naam chahiye", "Expected class name after 'varg'")
        args = []
        keywords = []
        if self.accept("("):
            if not self.accept(")"):
                while True:
                    if self.current().type == "NAME" and self.peek().type == "=":
                        kw_name = self.advance().value
                        self.advance()
                        keywords.append(N.keyword(arg=kw_name, value=self.parse_expression()))
                    else:
                        args.append(self.parse_expression())
                    if not self.accept(","):
                        break
                self.expect(")", "')' chahiye", "Expected ')'")
        body = self.parse_block()
        return N.ClassDef(name=name_tok.value, bases=args, keywords=keywords,
                          body=body, decorators=list(decorators or []))

    def parse_star_target(self):
        first = self._parse_star_one()
        elts = [first]
        while self.accept(","):
            if self.current().type in ("NEWLINE", "IN", ")"):
                break
            elts.append(self._parse_star_one())
        if len(elts) == 1:
            return first
        return N.Tuple(elts=elts)

    def _parse_star_one(self):
        if self.accept("*"):
            return N.Starred(value=self.parse_atom())
        return self.parse_atom()

    # ---------- expressions ----------

    def parse_expression(self):
        if self.current().type == "LAMBDA":
            return self.parse_lambda()
        if self.current().type == "NAME" and self.peek().type == ":=":
            name = self.advance().value
            self.advance()
            value = self.parse_expression()
            return N.NamedExpr(target=N.Name(id=name), value=value)
        return self.parse_if_exp()

    def parse_if_exp(self):
        body = self.parse_or_test()
        if self.accept("IF"):
            test = self.parse_or_test()
            self.expect("ELSE", "'warna' chahiye agar ke baad", "Expected 'warna' in conditional expression")
            orelse = self.parse_if_exp()
            return N.ConditionalExp(body=body, test=test, orelse=orelse)
        return body

    def parse_lambda(self):
        self.advance()
        params = []
        if self.current().type != ":":
            params = self.parse_params_inline()
        self.expect(":", "banao ke baad ':' chahiye", "Expected ':' in lambda")
        body = self.parse_expression()
        return N.Lambda(params=params, body=body)

    def parse_params_inline(self):
        params = []
        seen_star = False
        while True:
            if self.accept("**"):
                name = self.expect("NAME", "Naam chahiye", "Expected name").value
                params.append(N.Param(name=name, default=None, annotation=None, kind="kwarg"))
            elif self.accept("*"):
                seen_star = True
                if self.current().type == "NAME":
                    name = self.advance().value
                    params.append(N.Param(name=name, default=None, annotation=None, kind="vararg"))
                else:
                    params.append(N.Param(name="", default=None, annotation=None, kind="staronly"))
            else:
                name = self.expect("NAME", "Naam chahiye", "Expected parameter name").value
                default = None
                if self.accept("="):
                    default = self.parse_expression()
                kind = "pos" if not seen_star else "kwonly"
                params.append(N.Param(name=name, default=default, annotation=None, kind=kind))
            if not self.accept(","):
                break
        return params

    def parse_or_test(self):
        values = [self.parse_and_test()]
        while self.accept("OR"):
            values.append(self.parse_and_test())
        if len(values) == 1:
            return values[0]
        return N.BoolOp(op="or", values=values)

    def parse_and_test(self):
        values = [self.parse_not_test()]
        while self.accept("AND"):
            values.append(self.parse_not_test())
        if len(values) == 1:
            return values[0]
        return N.BoolOp(op="and", values=values)

    def parse_not_test(self):
        if self.accept("NOT"):
            operand = self.parse_not_test()
            return N.UnaryOp(op="not", operand=operand)
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_bitwise_or()
        ops = []
        comparators = []
        while True:
            tok = self.current()
            if tok.type in ("<", "<=", ">", ">=", "==", "!="):
                self.advance()
                ops.append(tok.type)
                comparators.append(self.parse_bitwise_or())
            elif tok.type == "IN":
                self.advance()
                ops.append("in")
                comparators.append(self.parse_bitwise_or())
            elif tok.type == "NOT" and self.peek().type == "IN":
                self.advance(); self.advance()
                ops.append("not in")
                comparators.append(self.parse_bitwise_or())
            elif tok.type == "IS":
                self.advance()
                if self.accept("NOT"):
                    ops.append("is not")
                else:
                    ops.append("is")
                comparators.append(self.parse_bitwise_or())
            elif tok.type == "IS" and False:
                pass
            else:
                break
        if not ops:
            return left
        return N.Compare(left=left, ops=ops, comparators=comparators)

    def parse_bitwise_or(self):
        node = self.parse_bitwise_xor()
        while self.current().type == "|":
            self.advance()
            node = N.BinOp(left=node, op="|", right=self.parse_bitwise_xor())
        return node

    def parse_bitwise_xor(self):
        node = self.parse_bitwise_and()
        while self.current().type == "^":
            self.advance()
            node = N.BinOp(left=node, op="^", right=self.parse_bitwise_and())
        return node

    def parse_bitwise_and(self):
        node = self.parse_shift()
        while self.current().type == "&":
            self.advance()
            node = N.BinOp(left=node, op="&", right=self.parse_shift())
        return node

    def parse_shift(self):
        node = self.parse_add()
        while self.current().type in ("<<", ">>"):
            op = self.advance().type
            node = N.BinOp(left=node, op=op, right=self.parse_add())
        return node

    def parse_add(self):
        node = self.parse_mul()
        while self.current().type in ("+", "-"):
            op = self.advance().type
            node = N.BinOp(left=node, op=op, right=self.parse_mul())
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while self.current().type in ("*", "/", "//", "%", "@"):
            op = self.advance().type
            node = N.BinOp(left=node, op=op, right=self.parse_unary())
        return node

    def parse_unary(self):
        tok = self.current()
        if tok.type in ("+", "-", "~"):
            self.advance()
            operand = self.parse_unary()
            return N.UnaryOp(op=tok.type, operand=operand)
        return self.parse_power()

    def parse_power(self):
        base = self.parse_await_atom()
        if self.current().type == "**":
            self.advance()
            exp = self.parse_unary()
            return N.BinOp(left=base, op="**", right=exp)
        return base

    def parse_await_atom(self):
        if self.accept("AWAIT"):
            return N.Await(value=self.parse_await_atom())
        return self.parse_atom()

    def parse_atom(self):
        tok = self.current()

        if tok.type == "NUMBER":
            self.advance()
            node = N.Constant(value=tok.value)
            return self.parse_trailers(node)

        if tok.type == "STRING":
            parts = [self.advance()]
            while self.current().type == "STRING":
                parts.append(self.advance())
            if len(parts) == 1:
                node = N.Constant(value=parts[0].value)
            else:
                node = N.Constant(value=" ".join(p.value for p in parts))
            return self.parse_trailers(node)

        if tok.type == "TRUE":
            self.advance(); node = N.Constant(value="True")
            return self.parse_trailers(node)
        if tok.type == "FALSE":
            self.advance(); node = N.Constant(value="False")
            return self.parse_trailers(node)
        if tok.type == "NONE":
            self.advance(); node = N.Constant(value="None")
            return self.parse_trailers(node)

        if tok.type == "NAME":
            self.advance()
            node = N.Name(id=tok.value)
            return self.parse_trailers(node)

        if tok.type == "(":
            self.advance()
            if self.accept(")"):
                return self.parse_trailers(N.Tuple(elts=[]))
            exprs = [self.parse_expression()]
            for_cmp = self.current().type == "FOR"
            if for_cmp:
                generators = self.parse_comprehension_clauses()
                node = N.GeneratorExp(elt=exprs[0], generators=generators)
                self.expect(")", "')' chahiye", "Expected ')'")
                return self.parse_trailers(node)
            trailing = False
            while self.accept(","):
                trailing = True
                if self.current().type == ")":
                    break
                exprs.append(self.parse_expression())
                trailing = False
            self.expect(")", "')' chahiye", "Expected ')'")
            if len(exprs) == 1 and not trailing:
                return self.parse_trailers(exprs[0])
            return self.parse_trailers(N.Tuple(elts=exprs))

        if tok.type == "[":
            self.advance()
            if self.accept("]"):
                return self.parse_trailers(N.List(elts=[]))
            first = self.parse_expression()
            if self.current().type == "FOR":
                generators = self.parse_comprehension_clauses()
                self.expect("]", "']' chahiye", "Expected ']'")
                return self.parse_trailers(N.ListComp(elt=first, generators=generators))
            elts = [first]
            while self.accept(","):
                if self.current().type == "]":
                    break
                elts.append(self.parse_expression())
            self.expect("]", "']' chahiye", "Expected ']'")
            return self.parse_trailers(N.List(elts=elts))

        if tok.type == "{":
            self.advance()
            if self.accept("}"):
                return self.parse_trailers(N.Dict(keys=[], values=[]))
            if self.current().type == "**":
                keys = []
                values = []
                while True:
                    if self.accept("**"):
                        keys.append(None)
                        values.append(self.parse_expression())
                    else:
                        key = self.parse_expression()
                        self.expect(":", "dict me ':' chahiye", "Expected ':' in dict")
                        value = self.parse_expression()
                        keys.append(key)
                        values.append(value)
                    if self.current().type == "FOR":
                        self._reject_dict_comp_unpack(keys, values)
                        generators = self.parse_comprehension_clauses()
                        self.expect("}", "'}' chahiye", "Expected '}'")
                        return self.parse_trailers(N.DictComp(key=keys[-1], value=values[-1], generators=generators))
                    if not self.accept(","):
                        break
                self.expect("}", "'}' chahiye", "Expected '}'")
                return self.parse_trailers(N.Dict(keys=keys, values=values))
            first_key = self.parse_expression()
            if self.current().type == "FOR":
                generators = self.parse_comprehension_clauses()
                self.expect("}", "'}' chahiye", "Expected '}'")
                return self.parse_trailers(N.SetComp(elt=first_key, generators=generators))
            self.expect(":", "dict me ':' chahiye (ya set likhiye to '{x, y}')", "Expected ':' in dict literal")
            first_value = self.parse_expression()
            keys = [first_key]
            values = [first_value]
            while self.accept(","):
                if self.current().type == "}":
                    break
                if self.accept("**"):
                    keys.append(None)
                    values.append(self.parse_expression())
                    continue
                key = self.parse_expression()
                self.expect(":", "dict me ':' chahiye", "Expected ':' in dict")
                value = self.parse_expression()
                keys.append(key)
                values.append(value)
            if self.current().type == "FOR":
                generators = self.parse_comprehension_clauses()
                self.expect("}", "'}' chahiye", "Expected '}'")
                return self.parse_trailers(N.DictComp(key=keys[-1], value=values[-1], generators=generators))
            self.expect("}", "'}' chahiye", "Expected '}'")
            return self.parse_trailers(N.Dict(keys=keys, values=values))

        if tok.type == "AWAIT":
            self.advance()
            return self.parse_trailers(N.Await(value=self.parse_await_atom()))

        got = tok.type if tok.type not in ("NAME", "STRING", "NUMBER") else repr(tok.value)
        raise HinglishError(tok.line,
                            f"Yahaan expression chahiye thi (mile: {got})",
                            f"Expected an expression (got: {got})")

    def _reject_dict_comp_unpack(self, keys, values):
        if None in keys:
            raise HinglishError(self.current().line,
                                "** wali unpack dict comprehension me nahi ho sakti",
                                "Cannot use ** unpacking in dict comprehension")

    def parse_comprehension_clauses(self):
        generators = []
        while self.accept("FOR"):
            target = self.parse_star_target()
            self.expect("IN", "har ke baad 'me' chahiye", "Expected 'me' in comprehension")
            iter_ = self.parse_or_test()
            ifs = []
            while self.accept("IF"):
                ifs.append(self.parse_or_test())
            generators.append(N.Comprehension(target=target, iter=iter_, ifs=ifs, is_async=False))
        return generators

    def parse_trailers(self, node):
        while True:
            tok = self.current()
            if tok.type == "(":
                self.advance()
                args, keywords = self.parse_call_args()
                node = N.Call(func=node, args=args, keywords=keywords)
            elif tok.type == "[":
                self.advance()
                node = N.Subscript(value=node, slice=self.parse_subscript())
            elif tok.type == ".":
                self.advance()
                attr = self.expect("NAME", "'.' ke baad attribute ka naam chahiye", "Expected attribute name after '.'")
                node = N.Attribute(value=node, attr=attr.value)
            else:
                break
        return node

    def parse_call_args(self):
        args, keywords = self.parse_comma_args({")"})
        self.expect(")", "')' chahiye", "Expected ')'")
        return args, keywords

    def parse_comma_args(self, terminators):
        args = []
        keywords = []
        if self.current().type in terminators:
            return args, keywords
        while True:
            if self.current().type == "**":
                self.advance()
                keywords.append(N.keyword(arg=None, value=self.parse_expression()))
            elif self.current().type == "*":
                self.advance()
                args.append(N.Starred(value=self.parse_expression()))
            elif self.current().type == "NAME" and self.peek().type == "=":
                name = self.advance().value
                self.advance()
                keywords.append(N.keyword(arg=name, value=self.parse_expression()))
            else:
                args.append(self.parse_expression())
            if not self.accept(","):
                break
            if self.current().type in terminators:
                break
        return args, keywords

    def parse_subscript(self):
        lower = upper = step = None
        saw_colon = False
        if self.current().type != ":":
            lower = self.parse_expression()
        while self.current().type == ":":
            self.advance()
            saw_colon = True
            if self.current().type != "]" and self.current().type != ":":
                upper = self.parse_expression()
            if self.accept(":"):
                if self.current().type != "]":
                    step = self.parse_expression()
                break
            break
        if not saw_colon:
            self.expect("]", "']' chahiye", "Expected ']'")
            return lower
        self.expect("]", "']' chahiye", "Expected ']'")
        return N.Slice(lower=lower, upper=upper, step=step)

    # ---------- match / case ----------

    def parse_match(self):
        self.advance()
        subject = self.parse_expression()
        self.expect(":", "match subject ke baad ':' chahiye", "Expected ':' after match subject")
        self.expect("NEWLINE", "Line khatam karo", "Expected end of line")
        self.skip_newlines()
        self.expect("INDENT", "match ke andar 'case' wali lines chahiye", "Expected indented case blocks")
        self.skip_newlines()
        cases = []
        while self.current().type == "CASE":
            cases.append(self.parse_case())
            self.skip_newlines()
        if not cases:
            raise HinglishError(self.current().line,
                                "match me kam se kam ek 'case' chahiye",
                                "match needs at least one 'case'")
        self.expect("DEDENT", "Indent sahi band nahi hui", "Expected dedent")
        return N.Match(subject=subject, cases=cases)

    def parse_case(self):
        self.advance()
        pattern = self.parse_pattern()
        guard = None
        if self.accept("IF"):
            guard = self.parse_expression()
        body = self.parse_block()
        return N.Case(pattern=pattern, guard=guard, body=body)

    def parse_pattern(self):
        node = self.parse_as_pattern()
        values = [node]
        while self.accept("|"):
            values.append(self.parse_as_pattern())
        if len(values) == 1:
            return values[0]
        return N.OrPattern(values=values)

    def parse_as_pattern(self):
        node = self.parse_primary_pattern()
        if self.accept("AS"):
            name = self.expect("NAME", "'jaise' ke baad naam chahiye", "Expected name after jaise").value
            return N.AsPattern(pattern=node, name=name)
        return node

    def parse_primary_pattern(self):
        tok = self.current()

        if tok.type == "-":
            self.advance()
            num = self.expect("NUMBER", "'-' ke baad number chahiye", "Expected number after '-'").value
            return N.LiteralPattern(value="-" + num)
        if tok.type == "NUMBER":
            self.advance()
            return N.LiteralPattern(value=tok.value)
        if tok.type == "STRING":
            self.advance()
            return N.LiteralPattern(value=tok.value)
        if tok.type in ("TRUE", "FALSE", "NONE"):
            self.advance()
            return N.LiteralPattern(value={"TRUE": "True", "FALSE": "False", "NONE": "None"}[tok.type])

        if tok.type == "(":
            self.advance()
            elts = [self.parse_pattern()]
            while self.accept(","):
                if self.current().type == ")":
                    break
                elts.append(self.parse_pattern())
            self.expect(")", "')' chahiye", "Expected ')'")
            if len(elts) == 1:
                return elts[0]
            return N.SequencePattern(elts=elts, bracket="(")

        if tok.type in ("[",):
            self.advance()
            elts = self._parse_sequence_elts("]")
            self.expect("]", "']' chahiye", "Expected ']'")
            return N.SequencePattern(elts=elts, bracket="[")

        if tok.type == "{":
            self.advance()
            pairs = []
            rest = None
            if self.current().type != "}":
                while True:
                    if self.accept("**"):
                        rest = self.expect("NAME", "'**' ke baad naam chahiye", "Expected name after '**'").value
                        break
                    key_tok = self.current()
                    if key_tok.type == "STRING":
                        key = N.LiteralPattern(value=self.advance().value)
                    elif key_tok.type == "NUMBER":
                        key = N.LiteralPattern(value=self.advance().value)
                    elif key_tok.type in ("TRUE", "FALSE", "NONE"):
                        key = N.LiteralPattern(value={"TRUE": "True", "FALSE": "False", "NONE": "None"}[key_tok.type])
                        self.advance()
                    else:
                        raise HinglishError(key_tok.line,
                                            "dict ka key literal hona chahiye",
                                            "Dict pattern keys must be literals")
                    self.expect(":", "':' chahiye", "Expected ':' in dict pattern")
                    value = self.parse_pattern()
                    pairs.append(N.MapPair(key=key, pattern=value))
                    if not self.accept(","):
                        break
            self.expect("}", "'}' chahiye", "Expected '}'")
            return N.MappingPattern(pairs=pairs, rest=rest)

        if tok.type == "NAME":
            name = tok.value
            if name == "_":
                self.advance()
                return N.WildcardPattern()
            dotted = [self.advance().value]
            while self.accept("."):
                dotted.append(self.expect("NAME", "'.' ke baad naam chahiye", "Expected name after '.'").value)
            dotted = ".".join(dotted)
            if self.current().type == "(":
                self.advance()
                args = []
                kwargs = []
                if not self.accept(")"):
                    while True:
                        if self.current().type == "NAME" and self.peek().type == "=":
                            kw_name = self.advance().value
                            self.advance()
                            kwargs.append(N.ClassKw(name=kw_name, pattern=self.parse_pattern()))
                        else:
                            args.append(self.parse_pattern())
                        if not self.accept(","):
                            break
                    self.expect(")", "')' chahiye", "Expected ')'")
                return N.ClassPattern(dotted=dotted, args=args, kwargs=kwargs)
            if "." in dotted:
                return N.ValuePattern(dotted=dotted)
            return N.CapturePattern(name=dotted)

        got = tok.type if tok.type not in ("NAME", "STRING", "NUMBER") else repr(tok.value)
        raise HinglishError(tok.line,
                            f"Yeh pattern nahi ban sakta (mile: {got})",
                            f"Not a valid pattern (got: {got})")

    def _parse_sequence_elts(self, close):
        elts = []
        while True:
            if self.current().type == close:
                break
            if self.accept(","):
                continue
            if self.accept("*"):
                tok = self.current()
                if tok.type == "NAME":
                    elts.append(N.StarPattern(name=self.advance().value))
                else:
                    raise HinglishError(tok.line,
                                        "'*' ke baad naam ya '_' chahiye",
                                        "Expected name or '_' after '*'")
                continue
            elts.append(self.parse_pattern())
            if not self.accept(","):
                break
        return elts
