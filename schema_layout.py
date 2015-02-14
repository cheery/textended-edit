from boxmodel import *
from metaschema import schema
from schema import Rule, ListRule


def page(env, subj):
    context = Object(env=env, outboxes=[])
    tokens = []
    for node in subj:
        tokens.extend(layout_element(context, node))
    return vpack(tokens), context.outboxes

globs = globals()

def layout_element(context, subj):
    def _layout(slot, subj):
        result = schema.recognize(subj)
        if isinstance(result, ListRule):
            name = 'rule_' + result.label.replace('-', '_')
            if name in globs:
                return globs[name](context, result.build(_layout, subj))
            tokens = plaintext(context.env, subj.label, color=context.env.blue)
            for subnode in subj:
                tokens.append(Glue(2))
                tokens.extend(_layout(None, subnode))
            return [hpack(tokens)]
        elif isinstance(result, Rule):
            name = 'rule_' + result.label.replace('-', '_')
            if name in globs:
                return globs[name](context, subj)
            return [hpack(plaintext(context.env, "Rule:" + result.label))]
        elif result == 'symbol':
            return plaintext(context.env, subj)
        elif result == 'blank':
            box = hpack(plaintext(context.env, "___"))
            box.set_subj(subj, 0)
            return [box]
        elif result == 'list' and subj.label == '@':
            tokens = []
            for subnode in subj:
                tokens.append(hpack(_layout(None, subnode)))
            outbox = Padding(vpack(tokens), (4, 4, 4, 4), Patch9("assets/border-1px.png"))
            anchor = ImageBox(10, 10, 2, None, context.env.white)
            context.outboxes.append((anchor, outbox))
            return [anchor]
        else:
            return [hpack(plaintext(context.env, result + ":" + subj.label))]
    return _layout(None, subj)

def rule_language(context, string):
    return [hpack(plaintext(context.env, string, color=context.env.yellow))]

def rule_toplevel(context, (name,)):
    return [hpack(
        plaintext(context.env, "toplevel ", color=context.env.blue) + name)]

def rule_bind(context, (lhs, rhs)):
    return [hpack(lhs + plaintext(context.env, " --> ", color=context.env.blue) +
        [vtop(hpacks(rhs))])]

def rule_rule(context, (name, lhs, rhs)):
    sp = plaintext(context.env, " ", color=context.env.blue)
    sp2 = plaintext(context.env, " ==> ", color=context.env.blue)
    return [hpack(name + sp + [vtop(hpacks(lhs))] + sp2 + rhs)]

def rule_sequence(context, seq):
    tokens = []
    for subtokens in seq:
        if len(tokens) > 0:
            tokens.append(Glue(4))
        tokens.extend(subtokens)
    return [hpack(tokens)]

def rule_star(context, (node,)):
    return [hpack(node + plaintext(context.env, "*", color=context.env.blue))]

def rule_plus(context, (node,)):
    return [hpack(node + plaintext(context.env, "+", color=context.env.blue))]

def flatten(seq):
    out = []
    for subseq in seq:
        out.extend(subseq)
    return out

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

class Object(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])
