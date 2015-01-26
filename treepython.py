#!/usr/bin/env python
import dom, sys, os, ast, imp
from collections import defaultdict
from recognizer import Group, String, Symbol, Context

grammar = defaultdict(list)

alias = Context('alias')
stmt = Context('stmt')
expr = Context('expr')
argument = Context('argument')
expr_set = Context('expr=')
subscript = Context('subscript')

def translate_pattern(env, node, pattern):#, func=None):
    result = pattern.scan(grammar, node)
    if result is None:
        raise TranslationError(node, pattern)
    match, context = result
    if isinstance(match, Group):
        gen = iter(node)
        out = [translate_pattern(env, gen.next(), pat) for pat in match.args]
        if match.varg:
            out.append([translate_pattern(env, rem, match.varg) for rem in gen])
        if callable(match.post):
            out = match.post(env, *out)
    else:
        out = node[:]
        if callable(match.post):
            out = match.post(env, out)
    for c in context:
        if callable(c.post):
            out = c.post(env, out)
    return out

class TranslationError(Exception):
    def __init__(self, node, pattern):
        self.node = node
        self.pattern = pattern

    @property
    def string(self):
        return "does not translate to {}".format(self.pattern)

    def __str__(self):
        return "{} does not translate to {}".format(self.node, self.pattern)

def semantic(ctx, pattern):
    def _impl_(func):
        pattern.post = func
        grammar[ctx.name].append(pattern)
        return func
    return _impl_

def as_python_sym(name):
    return intern(name.encode('utf-8'))

@semantic(stmt, Group('return', [expr]))
def return_statement(env, expr):
    return ast.Return(expr, lineno=0, col_offset=0)

@semantic(stmt, Group('print', [], expr))
def print_statement(env, exprs):
    return ast.Print(None, exprs, True, lineno=0, col_offset=0)

@semantic(stmt, Group('import', [], alias))
def import_statement(env, aliases):
    return ast.Import(aliases, lineno=0, col_offset=0)

@semantic(alias, Symbol())
def symbol_alias(env, name):
    return ast.alias(as_python_sym(name), None)

@semantic(stmt, Group('define', [Symbol(), Group('', [], Symbol())],stmt))
def def_statement(env, name, arglist, statements):
    return ast.FunctionDef(
        as_python_sym(name),
        ast.arguments([
            ast.Name(as_python_sym(a), ast.Param(), lineno=0, col_offset=0)
            for a in arglist[0]], None, None, []),
        statements, 
        [], lineno=0, col_offset=0)

@semantic(stmt, Context('expr'))
def expr_as_statement(env, expr):
    return ast.Expr(expr, lineno=0, col_offset=0)

@semantic(expr, Symbol())
def symbol_expression(env, symbol):
    if symbol[:1].isdigit():
        if '.' in symbol:
            return ast.Num(float(symbol), lineno=0, col_offset=0)
        return ast.Num(int(symbol), lineno=0, col_offset=0)
    else:
        return ast.Name(as_python_sym(symbol), ast.Load(), lineno=0, col_offset=0)

@semantic(expr, String(''))
def string_expression(env, string):
    return ast.Str(string, lineno=0, col_offset=0)

@semantic(expr, Group('attr', [expr, Symbol()]))
def attr_expression(env, subj, name):
    return ast.Attribute(subj, as_python_sym(name), ast.Load(), lineno=0, col_offset=0)

@semantic(stmt, Group('assign', [expr_set, expr]))
def assign_expression(env, target, value):
    return ast.Assign([target], value, lineno=0, col_offset=0)

@semantic(argument, Context('expr'))
def expr_as_argument(env, expr):
    return ('arg', expr)

@semantic(argument, Group('vararg', [expr]))
def varg_argument(env, expr):
    return ('vararg', expr)

@semantic(expr, Group('', [expr], argument))
def call_expression(env, func, argv):
    args = []
    varg = None
    for style, expr in argv:
        if style == 'arg':
            args.append(expr)
        elif style == 'vararg':
            varg = expr
        else:
            assert False, "should not happen"
    return ast.Call(func, args, [], varg, None, lineno=0, col_offset=0)

@semantic(expr, String("float-rgba"))
def float_rgba_expression(env, hexdec):
    channels = [c / 255.0 for c in hex_to_rgb(hexdec)] + [1.0]
    return ast.Tuple(
        [ast.Num(x, lineno=0, col_offset=0) for x in channels[:4]],
        ast.Load(),
        lineno=0, col_offset=0)

def hex_to_rgb(value):
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

@semantic(subscript, Context('expr'))
def expr_subscript(env, expr):
    return ast.Index(expr, lineno=0, col_offset=0)

@semantic(expr, Group('sub', [expr, subscript]))
def subscript_expr(env, value, slic):
    return ast.Subscript(value, slic, ast.Load(), lineno=0, col_offset=0)

@semantic(expr_set, Group('sub', [expr, subscript]))
def subscript_expr_set(env, value, slic):
    return ast.Subscript(value, slic, ast.Store(), lineno=0, col_offset=0)

@semantic(expr_set, Symbol())
def symbol_store(env, name):
    return ast.Name(as_python_sym(name), ast.Store(), lineno=0, col_offset=0)

@semantic(expr_set, Group('attr', [expr, Symbol()]))
def attr_expression(env, subj, name):
    return ast.Attribute(subj, as_python_sym(name), ast.Store(), lineno=0, col_offset=0)

def put_error_string(errors, node, message):
    if node.document.filename is not None:
        error = dom.Literal("", u"reference", [
            dom.Literal("", u"", node.ident),
            dom.Literal("", u"", unicode(node.document.filename)),
            dom.Literal("", u"", [dom.Literal("", u"", unicode(message))])])
    else:
        error = dom.Literal("", u"reference", [
            dom.Literal("", u"", node.ident),
            dom.Literal("", u"", [dom.Literal("", u"", unicode(message))])])
    errors.append(error)

class Env(object):
    def __init__(self):
        self.errors = [] 

class SemanticErrors(Exception):
    def __init__(self, document, filename):
        self.document = document
        self.filename = filename

    def __str__(self):
        return "{}".format(self.filename)

local_environ = dict()

def evaluate_document(document):
    ast = document_as_ast(document)
    if ast:
        exec compile(ast, "t+", 'exec') in local_environ

def file_as_ast(path):
    document = dom.Document(dom.Literal("", u"", dom.load(path)), path)
    return document_as_ast(document)

def document_as_ast(document):
    for item in document.body:
        if item.label == 'language':
            language = item[:]
            break
    else:
        return
    if language != 'python':
        return
    statements = []
    env = Env()
    for item in document.body:
        if item.label == 'language':
            assert item[:] == 'python'
        else:
            try:
                pattern = translate_pattern(env, item, stmt)
                statements.append(pattern)
            except TranslationError as error:
                put_error_string(env.errors, error.node, error.string)
    if env.errors:
        raise SemanticErrors(dom.Document(dom.Literal("", u"", env.errors)), document.filename)
    return ast.Module(statements)

def import_file_to_module(module_name, path):
    try:
        ast = file_as_ast(path)
        mod = imp.new_module(module_name)
        mod.__file__ = path
        eval(ast_compile(ast, path, "exec"), mod.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return mod

def ast_compile(ast, filename, mode):
    return compile(ast, filename, mode)

class MetaLoader(object):
    def __init__(self, path, ispkg):
        self.path = path
        self.ispkg = ispkg

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        sys.modules[fullname] = None
        mod = import_file_to_module(fullname, self.path)

        mod.__file__ = self.path
        mod.__loader__ = self
        mod.__name__ = fullname

        if self.ispkg:
            mod.__path__ = []
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]

        sys.modules[fullname] = mod
        return mod

class MetaImporter(object):
    def find_on_path(self, fullname):
        files = [("{}/{}/__init__.t+", True), ("{}/{}.t+", False)]
        dirpath = "/".join(fullname.split("."))
        for path in sys.path:
            path = os.path.abspath(path)
            for fp, ispkg in files:
                fullpath = fp.format(path, dirpath)
                if os.path.exists(fullpath):
                    return fullpath, ispkg
        return None, None

    def find_module(self, fullname, path=None):
        path, ispkg = self.find_on_path(fullname)
        if path:
            return MetaLoader(path, ispkg)

sys.meta_path.insert(0, MetaImporter())

if __name__=='__main__':
    try:
        sys.argv.pop(0)
        if len(sys.argv) > 0:
            import_file_to_module("__main__", sys.argv[0])
            sys.exit(0)
        else:
            sys.stderr.write("usage: treepython.py FILE\n")
            sys.exit(1)
    except SemanticErrors as ser:
        if not sys.stderr.isatty():
            dom.dump(sys.stderr, ser.document)
        else:
            print "semantic errors, route stderr to file"
        sys.exit(1)
