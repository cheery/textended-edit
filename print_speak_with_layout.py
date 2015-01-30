#!/usr/bin/env python
import dom
import sys
import pyttsx
import dom
from collections import defaultdict
from recognizer import Group, String, Symbol, Context

engine = pyttsx.init()
engine.setProperty('rate', 200)
engine.setProperty('voice', 'english')

grammar = defaultdict(list)

alias = Context('alias')
stmt = Context('stmt')
expr = Context('expr')
argument = Context('argument')
expr_set = Context('expr=')
subscript = Context('subscript')

def translate_pattern(env, node, pattern):#, func=None):
    "Converts the tree into alternative form."
    result = pattern.scan(grammar, node)
    if result is None:
        return print_out(node)
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

def semantic(ctx, pattern):
    "Tool to insert new rules into the grammar"
    def _impl_(func):
        pattern.post = func
        grammar[ctx.name].append(pattern)
        return func
    return _impl_

def print_out(node):
    "This is a fallback, in case the translate_pattern fails"
    if isinstance(node, dom.Symbol):
        return node.label + " ..."
    elif isinstance(node.contents, str):
        return node.label + " binary " + node.contents.encode('hex') + " ..."
    elif isinstance(node.contents, unicode):
        return node.label + " string " + node.contents + " ..."
    else:
        out = " begin " + node.label + " ..."
        for subnode in node:
            out += print_out(subnode)
        out += " end ..."
        return out

@semantic(stmt, Group('import', [], alias))
def import_stmt(env, aliases):
    return "import " + ', '.join(aliases) + " ..."

@semantic(stmt, Group('from-import', [Symbol()], alias))
def import_stmt(env, name, aliases):
    return "from " + name + " import " + ', '.join(aliases) + " ..."

@semantic(alias, Symbol())
def symbol_alias(env, sym):
    return sym

@semantic(stmt, Group('assign', [expr_set, expr]))
def assign_expr(env, lhs, rhs):
    return rhs + " assigned to " + lhs + " ..."

#@semantic(stmt, Group('return', [expr]))
#def return_stmt(env, expr):
#    engine.say("return " + expr)
#    return ''
#
@semantic(stmt, Group('print', [], expr))
def print_stmt(env, exprs):
    return "print " + ' '.join(exprs) + " ..."

@semantic(expr, String(""))
def string_expr(env, string):
    return "string " + string + ", "

path = sys.argv[1]
document = dom.Document(dom.Literal(u"", dom.load(path)), path)

for node in document.body.contents:
    if node.isstring() and node.label == 'language':
        assert node[:] == "python"
    else:
        engine.say( translate_pattern(None, node, stmt) )

engine.runAndWait()


# Next follows semantic rules recognised by treepython but not translated.

#@semantic(stmt, Group('print', [], expr))
#@semantic(stmt, Group('from-import', [Symbol()], alias))
#@semantic(stmt, Group('define', [Symbol(), Group('', [], Symbol())],stmt))
#@semantic(stmt, Group('if', [expr], stmt))
#@semantic(stmt, Group('while', [expr], stmt))
#@semantic(stmt, Context('expr'))
#@semantic(expr, Symbol())
#@semantic(expr, String(''))
#@semantic(expr, Group('attr', [expr, Symbol()]))
#@semantic(argument, Context('expr'))
#@semantic(argument, Group('vararg', [expr]))
#@semantic(expr, Group('cmp', [expr, Symbol(), expr]))
#@semantic(expr, Group('list', [], expr))
#@semantic(expr, Group('tuple', [], expr))
#@semantic(expr, Group('infix', [Symbol(), expr]))
#@semantic(expr, Group('infix', [expr, Symbol(), expr]))
#@semantic(expr, Group('', [expr], argument))
#@semantic(expr, String("float-rgba"))
#@semantic(subscript, Context('expr'))
#@semantic(expr, Group('sub', [expr, subscript]))
#@semantic(expr_set, Group('sub', [expr, subscript]))
#@semantic(expr_set, Symbol())
#@semantic(expr_set, Group('attr', [expr, Symbol()]))
