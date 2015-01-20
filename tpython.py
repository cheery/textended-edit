import dom
import ast
from collections import defaultdict

grammar = defaultdict(list)

class group(object):
    def __init__(self, label, *patterns):
        self.label = label
        self.patterns = patterns

class many(object):
    def __init__(self, pattern):
        self.pattern = pattern

class string_group(object):
    def __init__(self, label=None):
        self.label = label

def translate_pattern(env, node, pattern, func=None):
    if isinstance(pattern, str):
        results = []
        for subfunc, subpattern in grammar[pattern]:
            success, result = translate_pattern(env, node, subpattern, subfunc)
            if success:
                results.append(result)
        if len(results) == 0:
            return False, None
        if len(results) > 1:
            put_error_string(env.errors, node, "ambiguous as {}".format(pattern))
            return False, None
        if callable(func):
            return True, func(env, *results)
        return True, results[0]
    elif isinstance(pattern, group):
        if not (isinstance(node, dom.Literal) and isinstance(node.contents, list)):
            return False, None
        if pattern.label != node.label:
            return False, None
        subnodes = list(node[:])
        listing = []
        bad = False
        for subpattern in pattern.patterns:
            if isinstance(subpattern, many):
                sublisting = []
                while len(subnodes) > 0:
                    subnode = subnodes.pop(0)
                    success, result = translate_pattern(env, subnode, subpattern.pattern)
                    sublisting.append(result)
                    if not success:
                        bad = True
                        put_error_string(env.errors, subnode, "expected {}".format(subpattern))
                listing.append(sublisting)
            elif len(subnodes) == 0:
                bad = True
                put_error_string(env.errors, node, "append {}".format(subpattern))
            else:
                subnode = subnodes.pop(0)
                success, result = translate_pattern(env, subnode, subpattern)
                if not success:
                    bad = True
                    put_error_string(env.errors, subnode, "expected {}".format(subpattern))
                listing.append(result)
        if bad:
            return False, None
        if callable(func):
            return True,  func(env, *listing)
        return True, listing
    elif pattern is symbol:
        if isinstance(node, dom.Symbol):
            if callable(func):
                return True, func(env, node[:])
            else:
                return True, node[:]
    elif isinstance(pattern, string_group):
        if not (isinstance(node, dom.Literal) and isinstance(node.contents, unicode)):
            return False, None
        if pattern.label != node.label and pattern.label is not None:
            return False, None
        if callable(func):
            return True, func(env, node[:])
        else:
            return True, node[:]
    else:
        assert False, "{} func={}".format(pattern, func)
    return False, None

symbol = object()

def semantic(name, pattern):
    def _impl_(func):
        grammar[name].append((func, pattern))
        return func
    return _impl_

@semantic('stmt', group('print', many('expr')))
def print_statement(env, exprs):
    return ast.Print(None, exprs, True, lineno=0, col_offset=0)

@semantic('stmt', group('import', many('alias')))
def import_statement(env, aliases):
    return ast.Import(aliases, lineno=0, col_offset=0)

@semantic('alias', symbol)
def symbol_alias(env, name):
    return ast.alias(name.encode('utf-8'), None)

@semantic('stmt', group('define', symbol, group('', many(symbol)), many('stmt')))
def def_statement(env, name, arglist, statements):
    return ast.FunctionDef(
        name.encode('utf-8'),
        ast.arguments([
            ast.Name(a.encode('utf-8'), ast.Param(), lineno=0, col_offset=0)
            for a in arglist[0]], None, None, []),
        statements, 
        [], lineno=0, col_offset=0)

@semantic('stmt', 'expr')
def expr_as_statement(env, expr):
    return ast.Expr(expr, lineno=0, col_offset=0)

@semantic('expr', symbol)
def symbol_expression(env, symbol):
    if symbol[:1].isdigit():
        return ast.Num(int(symbol), lineno=0, col_offset=0)
    else:
        return ast.Name(symbol.encode('utf-8'), ast.Load(), lineno=0, col_offset=0)

@semantic('expr', string_group(''))
def string_expression(env, string):
    return ast.Str(string, lineno=0, col_offset=0)

@semantic('expr', group('attr', 'expr', symbol))
def attr_expression(env, subj, name):
    return ast.Attribute(subj, name.encode('utf-8'), ast.Load(), lineno=0, col_offset=0)

@semantic('stmt', group('assign', 'expr=', 'expr'))
def assign_expression(env, target, value):
    return ast.Assign([target], value, lineno=0, col_offset=0)

@semantic('expr', group('', 'expr', many('expr')))
def call_expression(env, func, argv):
    return ast.Call(func, argv, [], None, None, lineno=0, col_offset=0)

@semantic('expr=', symbol)
def symbol_store(env, name):
    return ast.Name(name.encode('utf-8'), ast.Store(), lineno=0, col_offset=0)

@semantic('expr=', group('attr', 'expr', symbol))
def attr_expression(env, subj, name):
    return ast.Attribute(subj, name.encode('utf-8'), ast.Store(), lineno=0, col_offset=0)

def put_error_string(errors, node, message):
    if isinstance(node, dom.Literal):
        errors.append(
            dom.Literal("", u"reference", [
                dom.Literal("", u"", node.ident),
                dom.Literal("", u"", [dom.Literal("", u"", unicode(message))])]))
    else:
        print 'warning: error string with no literal'

class Env(object):
    def __init__(self):
        self.errors = [] 

class SemanticErrors(Exception):
    def __init__(self, document):
        self.document = document

def evaluate_document(document):
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
            success, pattern = translate_pattern(env, item, 'stmt')
            if success:
                statements.append(pattern)
            else:
                put_error_string(env.errors, item, "expected stmt")
    if env.errors:
        raise SemanticErrors(dom.Document(dom.Literal("", u"", env.errors)))
    exec compile(ast.Module(statements), "t+", 'exec')
