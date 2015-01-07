import ast, sys, textended, os
from textended.common import Node

def translate_alias(alias):
    if alias.asname is None:
        return unicode(alias.name)
    else:
        return Node("", u"as", [unicode(alias.name), unicode(alias.asname)])

def translate_arguments(expr):
        return Node("", u"error", u"{}".format(stmt))

def translate_expr(expr):
        return Node("", u"error", u"{}".format(stmt))

def translate_stmt(stmt):
    if isinstance(stmt, ast.FunctionDef) and len(stmt.decorator_list) == 0:
        name = unicode(stmt.name)
        args = translate_arguments(stmt.args)
        body = [translate_stmt(st) for st in stmt.body]
        return Node("", u"def", [name, args] + body)
    elif isinstance(stmt, ast.Delete):
        contents = [translate_expr(target) for target in stmt.targets]
        return Node("", u"delete", contents)
    elif isinstance(stmt, ast.Assign):
        contents = [translate_expr(target) for target in stmt.targets]
        contents.append(translate_expr(stmt.value))
        return Node("", u"assign", contents)
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
        with open(filename, 'w') as fd:
            textended.dump(contents, fd)
