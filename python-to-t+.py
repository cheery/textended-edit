import ast, sys, textended, os
from textended.common import Node

def translate_alias(alias):
    if alias.asname is None:
        return unicode(alias.name)
    else:
        return Node("", u"as", [unicode(alias.name), unicode(alias.asname)])

def translate_arguments(arguments):
    arglist = [translate_expr(arg) for arg in arguments.args]
    if arguments.vararg is not None:
        arglist.append(Node("", u"vararg", unicode(arguments.vararg)))
    if arguments.kwarg is not None:
        arglist.append(Node("", u"kwarg", unicode(arguments.kwarg)))
    if len(arguments.defaults) > 0:
        return Node("", u"error", u"{}".format(arguments))
    return Node("", u"", arglist)

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
        op = {
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
            "FloorDiv": u"//"}[expr.op.__class__.__name__]
        return Node("", u"binop", [translate_expr(expr.left), op, translate_expr(expr.right)])
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
    elif isinstance(expr, ast.Attribute):
        return Node("", u"attr", [translate_expr(expr.value), unicode(expr.attr)])
    else:
        return Node("", u"error", u"{}".format(expr))

def translate_cond_stmt(stmt):
    if isinstance(stmt, ast.If):
        return Node("", u"if", [translate_expr(stmt.test)] + [translate_stmt(st) for st in stmt.body])
    else:
        return Node("", u"error", u"{}".format(stmt))

def translate_stmt(stmt):
    if isinstance(stmt, ast.FunctionDef) and len(stmt.decorator_list) == 0:
        name = unicode(stmt.name)
        args = translate_arguments(stmt.args)
        body = [translate_stmt(st) for st in stmt.body]
        return Node("", u"def", [name, args] + body)
    elif isinstance(stmt, ast.Return):
        if stmt.value is not None:
            ret = [translate_expr(stmt.value)]
        else:
            ret = []
        return Node("", u"return", ret)
    elif isinstance(stmt, ast.Delete):
        contents = [translate_expr(target) for target in stmt.targets]
        return Node("", u"delete", contents)
    elif isinstance(stmt, ast.Assign):
        contents = [translate_expr(target) for target in stmt.targets]
        contents.append(translate_expr(stmt.value))
        return Node("", u"assign", contents)
    elif hasattr(stmt, "orelse"):
        if len(stmt.orelse) == 0:
            return translate_cond_stmt(stmt)
        contents = [translate_cond_stmt(stmt)]
        while hasattr(stmt, 'orelse') and len(stmt.orelse) == 1:
            stmt = stmt.orelse[0]
            contents.append(translate_cond_stmt(stmt))
        if hasattr(stmt, 'orelse'):
            contents.append(Node("", u"", [translate_stmt(st) for st in stmt.orelse]))
        return Node("", u"cond", contents)
    elif isinstance(stmt, ast.Import):
        return Node("", u'import', [translate_alias(alias) for alias in stmt.names])
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
