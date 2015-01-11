import ast, sys, textended, os
from textended.common import Node

untranslated = set()

def translate_alias(alias):
    if alias.asname is None:
        return unicode(alias.name)
    else:
        return Node("", u"as", [unicode(alias.name), unicode(alias.asname)])

def translate_arguments(arguments):
    arglist = [translate_expr(arg) for arg in arguments.args]
    base = len(arguments.args) - len(arguments.defaults)
    for i, default in enumerate(arguments.defaults, base):
        arglist[i] = Node("", u"default", [arglist[i], translate_expr(default)])
    if arguments.vararg is not None:
        arglist.append(Node("", u"vararg", unicode(arguments.vararg)))
    if arguments.kwarg is not None:
        arglist.append(Node("", u"kwarg", unicode(arguments.kwarg)))
    return Node("", u"", arglist)

binops = {
    "Add": u"+",
    "Sub": u"-",
    "Mult": u"*",
    "Div": u"/",
    "Mod": u"%",
    "Pow": u"**",
    "LShift": u"<<",
    "RShift": u">>",
    "BitOr": u"|",
    "BitXor": u"^",
    "BitAnd": u"&",
    "FloorDiv": u"//"}

def translate_expr(expr):
    if isinstance(expr, ast.Name):
        return unicode(expr.id)
    elif isinstance(expr, ast.Num):
        return unicode(expr.n)
    elif isinstance(expr, ast.Str):
        return Node("", u"", unicode(expr.s))
    elif isinstance(expr, ast.UnaryOp):
        op = {"Invert": u"~", "Not": u"not", "UAdd": u"+", "USub": u"-"}[expr.op.__class__.__name__]
        return Node("", u"unaryop", [op, translate_expr(expr.operand)])
    elif isinstance(expr, ast.BinOp):
        op = binops[expr.op.__class__.__name__]
        return Node("", u"binop", [translate_expr(expr.left), op, translate_expr(expr.right)])
    elif isinstance(expr, ast.Lambda):
        return Node("", u"lambda", [translate_arguments(expr.args), translate_expr(expr.body)])
    elif isinstance(expr, ast.Compare):
        chain = [translate_expr(expr.left)]
        for op, right in zip(expr.ops, expr.comparators):
            chain.append({
                "Eq": u"==",
                "NotEq": u"!=",
                "Lt": u"<",
                "LtE": u"<=",
                "Gt": u">",
                "GtE": u">=",
                "Is": u"is",
                "IsNot": u"is-not",
                "In": u"in",
                "NotIn": u"not-in"}[op.__class__.__name__])
            chain.append(translate_expr(right))
        return Node("", u"compare", chain)
    elif isinstance(expr, ast.Call):
        arglist = [translate_expr(expr.func)]
        for arg in expr.args:
            arglist.append(translate_expr(arg))
        for kw in expr.keywords:
            arglist.append(Node("", u"keyword", [unicode(kw.arg), translate_expr(kw.value)]))
        if expr.starargs is not None:
            arglist.append(Node("", u"vararg", translate_expr(expr.starargs)))
        if expr.kwargs is not None:
            arglist.append(Node("", u"kwarg", translate_expr(expr.kwargs)))
        return Node("", u"", arglist)
    elif isinstance(expr, ast.Dict):
        pairs = [Node("", u"", [translate_expr(key), translate_expr(value)]) for key, value in zip(expr.keys, expr.values)]
        return Node("", u"dict", pairs)
    elif isinstance(expr, ast.Attribute):
        return Node("", u"attr", [translate_expr(expr.value), unicode(expr.attr)])
    elif isinstance(expr, ast.List):
        return Node('', u"list", [translate_expr(elt) for elt in expr.elts])
    elif isinstance(expr, ast.Tuple):
        return Node('', u"list", [translate_expr(elt) for elt in expr.elts])
    elif isinstance(expr, ast.ListComp):
        contents = [translate_expr(expr.elt)]
        contents.extend(translate_comprehension(comp) for comp in expr.generators)
        return Node('', u"list-generator", contents)
    elif isinstance(expr, ast.SetComp):
        contents = [translate_expr(expr.elt)]
        contents.extend(translate_comprehension(comp) for comp in expr.generators)
        return Node('', u"set-generator", contents)
    elif isinstance(expr, ast.DictComp):
        contents = [translate_expr(expr.key), translate_expr(expr.value)]
        contents.extend(translate_comprehension(comp) for comp in expr.generators)
        return Node('', u"dict-generator", contents)
    elif isinstance(expr, ast.GeneratorExp):
        contents = [translate_expr(expr.elt)]
        contents.extend(translate_comprehension(comp) for comp in expr.generators)
        return Node('', u"generator", contents)
    elif isinstance(expr, ast.BoolOp) and isinstance(expr.op, ast.And):
        return Node('', u"and", [translate_expr(value) for value in expr.values])
    elif isinstance(expr, ast.BoolOp) and isinstance(expr.op, ast.Or):
        return Node('', u"or", [translate_expr(value) for value in expr.values])
    elif isinstance(expr, ast.Subscript):
        return Node('', u"item", [translate_expr(expr.value), translate_slice(expr.slice)])
    elif isinstance(expr, ast.IfExp):
        return Node('', u"if-exp", [translate_expr(expr.test), translate_expr(expr.body), translate_expr(expr.orelse)])
    elif isinstance(expr, ast.Yield):
        if expr.value is None:
            return Node('', u"yield", [])
        return Node('', u"yield", [translate_expr(expr.value)])
    else:
        return Node("", u"error", u"{}".format(expr))

def translate_comprehension(comp):
    contents = [translate_expr(comp.target), translate_expr(comp.iter)]
    contents.extend(translate_expr(expr) for expr in comp.ifs)
    return Node("", u"", contents)

def translate_slice(slice):
    if isinstance(slice, ast.Slice):
        contents = [
            u"None" if slice.lower is None else translate_expr(slice.lower),
            u"None" if slice.upper is None else translate_expr(slice.upper),
            u"None" if slice.step is None else translate_expr(slice.step),
        ]
        return Node("", u"slice", contents)
    elif isinstance(slice, ast.Index):
        return translate_expr(slice.value)
    else:
        return Node("", u"error", u"{}".format(slice))

def translate_cond_stmt(stmt):
    if isinstance(stmt, ast.If):
        return Node("", u"if", [translate_expr(stmt.test)] + [translate_stmt(st) for st in stmt.body])
    elif isinstance(stmt, ast.While):
        return Node("", u"while", [translate_expr(stmt.test)] + [translate_stmt(st) for st in stmt.body])
    elif isinstance(stmt, ast.For):
        return Node("", u"for", [translate_expr(stmt.target), translate_expr(stmt.iter)] + [translate_stmt(st) for st in stmt.body])
    elif isinstance(stmt, ast.TryExcept):
        body = [translate_stmt(st) for st in stmt.body]
        body.extend(translate_handler(handler) for handler in stmt.handlers)
        return Node("", u"try", body)
    else:
        return Node("", u"error", u"{}".format(stmt))

def translate_decorators(decorator_list, subj):
    return Node('', u"decorator", [translate_expr(deco) for deco in decorator_list] + [subj])

def translate_handler(handler):
    contents = []
    if handler.type is not None:
        contents.append(Node("", u"type", translate_expr(handler.type)))
    if handler.name is not None:
        contents.append(Node("", u"as", translate_expr(handler.name)))
    contents.extend(translate_stmt(st) for st in handler.body)
    return Node("", u"except", contents)

def translate_stmt(stmt):
    if isinstance(stmt, ast.FunctionDef):
        name = unicode(stmt.name)
        args = translate_arguments(stmt.args)
        body = [translate_stmt(st) for st in stmt.body]
        return translate_decorators(stmt.decorator_list, Node("", u"def", [name, args] + body))
    elif isinstance(stmt, ast.ClassDef):
        name = unicode(stmt.name)
        bases = Node("", u"bases", [translate_expr(expr) for expr in stmt.bases])
        body = [translate_stmt(st) for st in stmt.body]
        return translate_decorators(stmt.decorator_list, Node("", u"class", [name, bases] + body))
    elif isinstance(stmt, ast.Return):
        if stmt.value is not None:
            ret = [translate_expr(stmt.value)]
        else:
            ret = []
        return Node("", u"return", ret)
    elif isinstance(stmt, ast.Delete):
        contents = [translate_expr(target) for target in stmt.targets]
        return Node("", u"delete", contents)
    elif isinstance(stmt, ast.Assert):
        contents = [translate_expr(stmt.test)]
        if stmt.msg is not None:
            contents.append(translate_expr(stmt.msg))
        return Node("", u"assert", contents)
    elif isinstance(stmt, ast.Print):
        if stmt.dest is not None:
            dest = [Node("", u"dest", [translate_expr(stmt.dest)])]
        else:
            dest = []
        label = u"print-line" if stmt.nl else u"print"
        return Node("", label, dest + [translate_expr(value) for value in stmt.values])
    elif isinstance(stmt, ast.Global):
        return Node("", u"global", [unicode(name) for name in stmt.names])
    elif isinstance(stmt, ast.Assign):
        contents = [translate_expr(target) for target in stmt.targets]
        contents.append(translate_expr(stmt.value))
        return Node("", u"assign", contents)
    elif isinstance(stmt, ast.AugAssign):
        contents = [translate_expr(stmt.target), binops[stmt.op.__class__.__name__], translate_expr(stmt.value)]
        return Node("", u"aug-assign", contents)
    elif hasattr(stmt, "orelse"):
        if len(stmt.orelse) == 0:
            return translate_cond_stmt(stmt)
        contents = [translate_cond_stmt(stmt)]
        while len(stmt.orelse) == 1 and hasattr(stmt.orelse[0], 'orelse'):
            stmt = stmt.orelse[0]
            contents.append(translate_cond_stmt(stmt))
        if hasattr(stmt, 'orelse'):
            contents.append(Node("", u"", [translate_stmt(st) for st in stmt.orelse]))
        return Node("", u"cond", contents)
    elif isinstance(stmt, ast.With):
        contents = [translate_expr(stmt.context_expr)]
        if stmt.optional_vars is not None:
            contents.append(Node('', u'as', [translate_expr(stmt.optional_vars)]))
        contents.extend(translate_stmt(st) for st in stmt.body)
        return Node("", u"with", contents)
    elif isinstance(stmt, ast.TryFinally):
        body = Node("", u"", [translate_stmt(st) for st in stmt.body])
        fin = Node("", u"", [translate_stmt(st) for st in stmt.finalbody])
        return Node("", u"try-finally", [body, fin])
    elif isinstance(stmt, ast.ImportFrom):
        if stmt.level != 0:
            print "stmt level a number?", stmt.level
        return Node("", u'from-import', [unicode(stmt.module)] + [translate_alias(alias) for alias in stmt.names])
    elif isinstance(stmt, ast.Import):
        return Node("", u'import', [translate_alias(alias) for alias in stmt.names])
    elif isinstance(stmt, ast.Expr):
        return translate_expr(stmt.value)
    elif isinstance(stmt, ast.Exec):
        contents = [translate_expr(stmt.body)]
        if stmt.globals is not None:
            contents.append(Node("", u"globals", [translate_expr(stmt.globals)]))
        if stmt.locals is not None:
            contents.append(Node("", u"locals", [translate_expr(stmt.locals)]))
        return Node("", u"exec", contents)
    elif isinstance(stmt, ast.Raise):
        contents = []
        if stmt.type is not None:
            contents.append(Node("", u"type", [translate_expr(stmt.type)]))
        if stmt.inst is not None:
            contents.append(Node("", u"inst", [translate_expr(stmt.inst)]))
        if stmt.tback is not None:
            contents.append(Node("", u"tback", [translate_expr(stmt.tback)]))
        return Node("", u"raise", contents)
    elif isinstance(stmt, ast.Continue):
        return Node("", u"", u"continue")
    elif isinstance(stmt, ast.Break):
        return Node("", u"", u"break")
    elif isinstance(stmt, ast.Pass):
        return Node("", u"", u"pass")
    else:
        return Node("", u"error", u"{}".format(stmt))

if __name__=='__main__':
    for filename in sys.argv[1:]:
        with open(filename) as fd:
            source = fd.read()
        root = ast.parse(source, filename)
        contents = []
        contents.append(Node("", u"language", u"python"))
        for stmt in root.body:
            contents.append(translate_stmt(stmt))
        filename = os.path.splitext(filename)[0] + '.t+'
        with open(filename, 'wb') as fd:
            textended.dump(contents, fd)
