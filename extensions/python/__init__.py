import defaultlayout
import recognizer
import dom
from collections import defaultdict
from recognizer import Group, String, Symbol, Context
from boxmodel import *
from defaultlayout import sans

grammar = defaultdict(list)

alias = Context('alias')
stmt = Context('stmt')
expr = Context('expr')
expr_set = Context('expr=')

def translate_pattern(mapping, pattern):
    result = pattern.scan(grammar, mapping.subj)
    if result is None:
        return defaultlayout.build(mapping)
    match, context = result
    if isinstance(match, recognizer.Group):
        gen = iter(mapping)
        out = [gen.next().update(translate_pattern, pat) for pat in match.args]
        if match.varg:
            out.append([rem.update(translate_pattern, match.varg) for rem in gen])
        if callable(match.post):
            out = match.post(*out)
    else:
        if callable(match.post):
            out = match.post(mapping.subj)
        else:
            out = sans(mapping.subj, defaultlayout.fontsize, color=defaultlayout.white)
    for c in context:
        if callable(c.post):
            out = c.post(out)
    return out

def semantic(ctx, pattern):
    def _impl_(func):
        pattern.post = func
        grammar[ctx.name].append(pattern)
        return func
    return _impl_

@semantic(stmt, Group('return', [expr]))
def layout_return(expr):
    ret = sans('return ', defaultlayout.fontsize, color=defaultlayout.blue)
    yield hpack(ret + expr)

@semantic(stmt, Group('print', [], expr))
def layout_print(exprs):
    tokens = sans('print', defaultlayout.fontsize, color=defaultlayout.blue)
    for expr in exprs:
        tokens.extend(sans(' ', defaultlayout.fontsize))
        tokens.extend(expr)
    yield hpack(tokens)

@semantic(stmt, Group('import', [], alias))
def layout_import(aliases):
    tokens = sans('import', defaultlayout.fontsize, color=defaultlayout.blue)
    for alias in aliases:
        tokens.extend(sans(" ", defaultlayout.fontsize))
        tokens.extend(alias)
    yield hpack(tokens)

@semantic(alias, Symbol())
def layout_alias_symbol(node):
    return sans(node, defaultlayout.fontsize)

@semantic(stmt, Group('define', [Symbol(), Group('', [], Symbol())], stmt))
def layout_def(name, arglist, body):
    tokens = sans('def', defaultlayout.fontsize, color=defaultlayout.blue)
    tokens.extend(sans(" ", defaultlayout.fontsize))
    tokens.extend(name)
    tokens.extend(sans('(', defaultlayout.fontsize, color=defaultlayout.gray))
    for i, arg in enumerate(arglist[0]):
        if i > 0:
            tokens.extend(sans(" ", defaultlayout.fontsize))
        tokens.extend(arg)
    tokens.extend(sans('):', defaultlayout.fontsize, color=defaultlayout.gray))
    hpack(tokens)

    bodylist = []
    for stmt in body:
        bodylist.append(Glue(3))
        bodylist.extend(stmt)
    yield vpack([
        hpack(tokens),
        Padding(vpack(bodylist), (25, 0, 0, 0))])

@semantic(expr, Group('vararg', [expr]))
def varg_argument(expr):
    yield hpack(sans('*', defaultlayout.fontsize, color=defaultlayout.gray) + expr)

@semantic(expr, String("float-rgba"))
def float_rgba_expression(hexdec):
    try:
        channels = [c / 255.0 for c in hex_to_rgb(hexdec[:])] + [1.0]
        rgba = tuple(channels[:4])
    except ValueError as v:
        rgba = 1.0, 1.0, 1.0, 1.0
    prefix = sans(' #', defaultlayout.fontsize, color=defaultlayout.gray)
    text = sans(hexdec, defaultlayout.fontsize, color=defaultlayout.white)
    yield Padding(
            hpack([ImageBox(12, 10, 4, None, rgba)] + prefix + text),
            (1, 1, 1, 1),
            Patch9('assets/border-1px.png'))
    yield Glue(2)

def hex_to_rgb(value):
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

@semantic(stmt, Context('expr'))
def passthrough(exprs):
    return exprs

@semantic(expr, Group('attr', [expr, Symbol()]))
@semantic(expr_set, Group('attr', [expr, Symbol()]))
def layout_attr(expr, name):
    yield hpack(expr + sans('.', defaultlayout.fontsize) + name)

@semantic(stmt, Group('assign', [expr_set, expr]))
def layout_assign(lhs, rhs):
    yield hpack(lhs + sans(' = ', defaultlayout.fontsize, color=defaultlayout.gray) + rhs)

@semantic(expr, Group('', [expr],expr))
def layout_call(callee, arglist):
    base = list(callee)
    base.extend(sans('(', defaultlayout.fontsize, color=defaultlayout.gray))
    for i, tokens in enumerate(arglist):
        if i > 0:
            base.extend(sans(', ', defaultlayout.fontsize, color=defaultlayout.gray))
        base.extend(tokens)
    base.extend(sans(')', defaultlayout.fontsize, color=defaultlayout.gray))
    yield hpack(base)

def layout(mapping, *args):
    for submapping in mapping:
        for token in submapping.update(translate_pattern, stmt):
            yield token
            yield Glue(3)
