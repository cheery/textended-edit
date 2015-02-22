from boxmodel import *
from layout import vskip, packlines, sentinel

def toplevel(context, (name,)):
    return vskip([hpack(
        plaintext(context.env, "toplevel ", color=context.env.blue) + name)])

def bind(context, (lhs, rhs)):
    return vskip([vpack([
        hpack(
            plaintext(context.env, "bind ", color=context.env.blue) +
            lhs + 
            plaintext(context.env, " to", color=context.env.blue)),
        hpack([Glue(20), vtop(hpacks(rhs))]),
        ])])
#    return vskip([hpack(lhs + plaintext(context.env, " --> ", color=context.env.blue) +
#        [vtop(hpacks(rhs))])])

def rule(context, (name, lhs, rhs)):
    lb = plaintext(context.env, "  [", color=context.env.gray)
    rb = plaintext(context.env, "]", color=context.env.gray)
    tokens = []
    for boxes in lhs:
        if len(tokens) > 0:
            tokens.extend(plaintext(context.env, ", ", color=context.env.gray))
        tokens.extend(boxes)
    return vskip([vpack([
        hpack(name + lb + tokens + rb),
        hpack([Glue(20)] + rhs),
        ])])

    return vskip([hpack(name + sp + [vtop(hpacks(lhs))] + sp2 + rhs)])

def sequence(context, seq):
    tokens = []
    for subtokens in seq:
        if len(tokens) > 0:
            tokens.append(Glue(4))
        tokens.extend(subtokens)
    return [hpack(tokens)]

def star(context, (node,)):
    return [hpack(node + plaintext(context.env, "*", color=context.env.gray))]

def plus(context, (node,)):
    return [hpack(node + plaintext(context.env, "+", color=context.env.gray))]

def hpacks(seq):
    out = []
    for subseq in seq:
        out.append(hpack(subseq))
    return out

def vtop(seq):
    if len(seq) > 0:
        first = seq[0]
        box = vpack(seq)
        box.height += first.height
        box.depth -= first.height
        return box
    return vpack(seq)

def plaintext(env, text, fontsize=None, color=None):
    return env.font(text,
        env.fontsize if fontsize is None else fontsize,
        color = env.white if color is None else color)
