import defaultlayout
import recognizer
import dom
from collections import defaultdict
from recognizer import Group, String, Symbol, Context
from boxmodel import *

grammar = defaultdict(list)

alias = Context('alias')
stmt = Context('stmt')
expr = Context('expr')
expr_set = Context('expr=')
subscript = Context('subscript')

def translate_pattern(mapping, env, pattern):
    if mapping.subj.isblank():
        return defaultlayout.layout(mapping, env)
    result = pattern.scan(grammar, mapping.subj)
    if result is None:
        return defaultlayout.layout(mapping, env)
    match, context = result
    for c in reversed(context):
        if callable(c.pre):
            env = c.pre(mapping, env)
    if callable(match.pre):
        out = match.pre(mapping, env, match)
    elif isinstance(match, recognizer.Group):
        gen = iter(mapping)
        out = [gen.next().update(translate_pattern, env, pat) for pat in match.args]
        if match.varg:
            out.append([rem.update(translate_pattern, env, match.varg) for rem in gen])
        if callable(match.post):
            out = match.post(env, *out)
    else:
        if callable(match.post):
            out = match.post(env, mapping.subj)
        else:
            out = plaintext(env, mapping.subj)
    for c in context:
        if callable(c.post):
            out = c.post(env, out)
    return out

def group_with_env(mapping, group, envs):
    gen = iter(mapping)
    envs = iter(envs)
    out = [gen.next().update(translate_pattern, envs.next(), pat) for pat in group.args]
    if group.varg:
        out.append([rem.update(translate_pattern, envs.next(), group.varg) for rem in gen])
    return out

def pre_semantic(ctx, pattern):
    def _impl_(func):
        pattern.pre =  func
        if pattern not in grammar[ctx.name]:
            grammar[ctx.name].append(pattern)
        return func
    return _impl_

def semantic(ctx, pattern):
    def _impl_(func):
        pattern.post = func
        if pattern not in grammar[ctx.name]:
            grammar[ctx.name].append(pattern)
        return func
    return _impl_

@semantic(stmt, Group('return', [expr]))
def layout_return(env, expr):
    ret = plaintext(env, 'return', color=env['blue'])
    yield hpack(ret + expr)

@semantic(stmt, Group('print', [], expr))
def layout_print(env, exprs):
    tokens = plaintext(env, 'print', color=env['blue'])
    for expr in exprs:
        tokens.extend(plaintext(env, ' '))
        tokens.extend(expr)
    yield hpack(tokens)

@semantic(stmt, Group('import', [], alias))
def layout_import(env, aliases):
    tokens = plaintext(env, 'import', color=env['blue'])
    for alias in aliases:
        tokens.extend(plaintext(env, ' '))
        tokens.extend(alias)
    yield hpack(tokens)

@semantic(stmt, Group('from-import', [Symbol()], alias))
def layout_import(env, name, aliases):
    tokens = plaintext(env, 'from ', color=env['blue'])
    tokens += name
    tokens += plaintext(env, ' import', color=env['blue'])
    for alias in aliases:
        tokens.extend(plaintext(env, ' '))
        tokens.extend(alias)
    yield hpack(tokens)

@semantic(alias, Symbol())
def layout_alias_symbol(env, node):
    return plaintext(env, node)

@semantic(stmt, Group('define', [Symbol(), Group('', [], Symbol())], stmt))
def layout_def(env, name, arglist, body):
    tokens = plaintext(env, 'def ', color=env['blue'])
    tokens.extend(name)
    tokens.extend(plaintext(env, '(', color=env['gray']))
    for i, arg in enumerate(arglist[0]):
        if i > 0:
            tokens.extend(plaintext(env, " "))
        tokens.extend(arg)
    tokens.extend(plaintext(env, '):', color=env['gray']))

    bodylist = []
    for stmt in body:
        bodylist.append(Glue(3))
        bodylist.extend(stmt)
    yield vpack([
        hpack(tokens),
        Padding(vpack(bodylist), (25, 0, 0, 0))])

@semantic(stmt, Group('while', [expr], stmt))
def layout_whilwhile(env, cond, body):
    tokens = plaintext(env, 'while ', color=env['blue'])
    tokens.extend(cond)
    tokens.extend(plaintext(env, ':', color=env['blue']))

    bodylist = []
    for stmt in body:
        bodylist.append(Glue(3))
        bodylist.extend(stmt)
    yield vpack([
        hpack(tokens),
        Padding(vpack(bodylist), (25, 0, 0, 0))])

@semantic(stmt, Group('if', [expr], stmt))
def layout_if(env, cond, body):
    tokens = plaintext(env, 'if ', color=env['blue'])
    tokens.extend(cond)
    tokens.extend(plaintext(env, ':', color=env['blue']))

    bodylist = []
    for stmt in body:
        bodylist.append(Glue(3))
        bodylist.extend(stmt)
    yield vpack([
        hpack(tokens),
        Padding(vpack(bodylist), (25, 0, 0, 0))])

@semantic(expr, Group('vararg', [expr]))
def varg_argument(env, expr):
    yield hpack(plaintext(env, '*', color=env['gray']) + expr)

@semantic(expr, Group('list', [], expr))
def list_expression(env, exprs):
    tokens = []
    for expr in exprs:
        tokens.append(hpack(expr))
    yield Padding(
            vpack(tokens),
            (5, 0, 0, 0),
            Patch9('assets/border-left-1px.png'))

@semantic(expr, Group('tuple', [], expr))
def list_expression(env, exprs):
    tokens = []
    for expr in exprs:
        tokens.append(hpack(expr))
    yield Padding(
            vpack(tokens),
            (5, 0, 0, 0),
            Patch9('assets/border-left-1px.png'), color=(0, 1, 1, 1))

@semantic(expr, Group('cmp', [expr, Symbol(), expr]))
def cmp_expr(env, lhs, op, rhs):
    yield hpack(lhs + plaintext(env, ' ') + op + plaintext(env, ' ') + rhs)

@semantic(expr, Group('infix', [Symbol(), expr]))
def infix_expr(env, op, rhs):
    yield hpack(op + plaintext(env, ' ') + rhs)

@semantic(expr, Group('infix', [expr, Symbol(), expr]))
def infix_expr(env, lhs, op, rhs):
    yield hpack(lhs + plaintext(env, ' ') + op + plaintext(env, ' ') + rhs)

@semantic(expr, String("float-rgba"))
def float_rgba_expression(env, hexdec):
    try:
        channels = [c / 255.0 for c in hex_to_rgb(hexdec[:])] + [1.0]
        rgba = tuple(channels[:4])
    except ValueError as v:
        rgba = 1.0, 1.0, 1.0, 1.0
    prefix = plaintext(env, ' #', color=env['gray'])
    text = plaintext(env, hexdec, color=env['white'])
    yield Padding(
            hpack([ImageBox(12, 10, 4, None, rgba)] + prefix + text),
            (1, 1, 1, 1),
            Patch9('assets/border-1px.png'))
    yield Glue(2)

def hex_to_rgb(value):
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

@semantic(stmt, Context('expr'))
@semantic(subscript, Context('expr'))
def passthrough(env, exprs):
    return exprs

@semantic(subscript, String(""))
def without_quotes(env, subj):
    return plaintext(subj, color=env['yellow'])

@semantic(expr, Group('attr', [expr, Symbol()]))
@semantic(expr_set, Group('attr', [expr, Symbol()]))
def layout_attr(env, expr, name):
    yield hpack(expr + plaintext(env, '.') + name)

@pre_semantic(expr, Group('sub', [expr, subscript]))
@pre_semantic(expr_set, Group('sub', [expr, subscript]))
def pre_subscript(mapping, env, group):
    sub_env = env.copy()
    sub_env.update(fontsize=env['fontsize'] - 1)
    lhs, rhs = group_with_env(mapping, group, [env, sub_env])
    for r in rhs:
        r.shift = 4
    yield hpack(lhs + [Glue(-1)] + rhs)

@semantic(stmt, Group('assign', [expr_set, expr]))
def layout_assign(env, lhs, rhs):
    yield hpack(lhs + env['font'](' = ', env['fontsize'], color=env['gray']) + rhs)

@semantic(expr, Group('', [expr],expr))
def layout_call(env, callee, arglist):
    base = list(callee)
    base.extend(env['font']('(', env['fontsize'], color=env['gray']))
    for i, tokens in enumerate(arglist):
        if i > 0:
            base.extend(env['font'](', ', env['fontsize'], color=env['gray']))
        base.extend(tokens)
    base.extend(env['font'](')', env['fontsize'], color=env['gray']))
    yield hpack(base)

def plaintext(env, text, size=None, color=None):
    size = env['fontsize'] if size is None else size
    color = env['white'] if color is None else color
    return env['font'](text, size, color=color)

def layout(mapping, env):
    for submapping in mapping:
        for token in submapping.update(translate_pattern, env, stmt):
            yield token
            yield Glue(3)
