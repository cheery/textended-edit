from boxmodel import *

def toplevel(context, (name,)):
    return [hpack(
        plaintext(context.env, "toplevel ", color=context.env.blue) + name)]

def bind(context, (lhs, rhs)):
    return [hpack(lhs + plaintext(context.env, " --> ", color=context.env.blue) +
        [vtop(hpacks(rhs))])]

def rule(context, (name, lhs, rhs)):
    sp = plaintext(context.env, " ", color=context.env.blue)
    sp2 = plaintext(context.env, " ==> ", color=context.env.blue)
    return [hpack(name + sp + [vtop(hpacks(lhs))] + sp2 + rhs)]

def sequence(context, seq):
    tokens = []
    for subtokens in seq:
        if len(tokens) > 0:
            tokens.append(Glue(4))
        tokens.extend(subtokens)
    return [hpack(tokens)]

def star(context, (node,)):
    return [hpack(node + plaintext(context.env, "*", color=context.env.blue))]

def plus(context, (node,)):
    return [hpack(node + plaintext(context.env, "+", color=context.env.blue))]

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
