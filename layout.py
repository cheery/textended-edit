from boxmodel import *
from schema import Rule, ListRule, modeline, modechange, blankschema, has_modeline
import dom
import importlib

def page(workspace, env, subj):
    context = Object(workspace=workspace, env=env, outboxes=[], schema=blankschema, layout=None)
    tokens = []
    if has_modeline(subj):
        configure_schema(context, subj[0])
    for node in subj:
        tokens.extend(layout_element(context, node))
        tokens.append(separator(context.env))
    tokens.extend(sentinel(context.env, subj))
    return packlines(tokens, 400), context.outboxes

def configure_schema(context, modeline):
    schema_name = modeline[0][:]
    if schema_name == '':
        return blankschema
    context.schema = context.workspace.get_schema(schema_name)
    try:
        context.layout = importlib.import_module("layouts." + schema_name)
    except ImportError:
        context.layout = None

def layout_element(context, subj):
    def _layout(slot, subj):
        result = context.schema.recognize(subj)
        if isinstance(result, ListRule):
            name = result.label.replace('-', '_')
            if hasattr(context.layout, name):
                return getattr(context.layout, name)(context, result.build(_layout, subj))
            tokens = plaintext(context.env, subj.label, color=context.env.blue)
            for subnode in subj:
                tokens.append(Glue(2))
                tokens.extend(_layout(None, subnode))
            return [hpack(tokens)]
        elif isinstance(result, Rule):
            name = result.label.replace('-', '_')
            if hasattr(context.layout, name):
                return getattr(context.layout, name)(context, subj)
            return [hpack(plaintext(context.env, "Rule:" + result.label))]
        elif result in ('symbol', 'blank'):
            return plaintext(context.env, subj)
        elif result == 'list' and subj.label == '@':
            tokens = []
            for subnode in subj:
                tokens.extend(_layout(None, subnode))
                tokens.append(separator(context.env))
            outbox = Padding(packlines(tokens, 400), (4, 4, 4, 4), Patch9("assets/border-1px.png"))
            anchor = ImageBox(10, 10, 2, None, context.env.white)
            context.outboxes.append((anchor, outbox))
            return [anchor]
        elif result == 'string':
            pre = plaintext(context.env, '"', color=context.env.yellow)
            pos = plaintext(context.env, '"', color=context.env.yellow)
            return [hpack(pre + plaintext(context.env, subj, color=context.env.yellow) + pos)]
        elif result == '##':
            return layout_modeline(context, subj)
        else:
            return [hpack(plaintext(context.env, result + ":" + subj.label))]
    return _layout(None, subj)

def layout_modeline(context, modeline):
    tokens = []
    tokens.extend(plaintext(context.env, "##", color=context.env.blue))
    for sym in modeline:
        tokens.extend(plaintext(context.env, " "))
        tokens.extend(plaintext(context.env, sym))
    line = hpack(tokens)
    line.hint = {'vskip': True}
    return [line]

def plaintext(env, text, fontsize=None, color=None):
    if isinstance(text, dom.Symbol) and len(text) == 0:
        box = hpack(plaintext(env, "___"))
        box.set_subj(text, 0)
        return [box]
    return env.font(text,
        env.fontsize if fontsize is None else fontsize,
        color = env.white if color is None else color)

def sentinel(env, subj):
    if len(subj) == 0:
        yield ImageBox(10, 10, 5, None, env.gray).set_subj(subj, 0)

def packlines(tokens, width):
    out = []
    line = []
    total_width = 0
    greedy_cutpoint = -1
    for token in tokens:
        if (token.vsize > 20 and not isinstance(token, Glue)) or token.get_hint('vskip', False):
            if len(line) > 0:
                out.append(hpack(line))
            out.append(token)
            line = []
            greedy_cutpoint = -1
            total_width = 0
        else:
            if token.get_hint('break', False):
                if len(line) == 0:
                    continue
                greedy_cutpoint = len(line)
            line.append(token)
            total_width += token.width
            if total_width > width and greedy_cutpoint >= 0:
                out.append(hpack(line[:greedy_cutpoint+1]))
                line = line[greedy_cutpoint+1:]
                total_width = sum(item.width for item in line)
    if len(line) > 0:
        out.append(hpack(line))
    return vpack(out)

class Object(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])

def separator(env):
    glue = Glue(4)
    glue.hint = {'break': True}
    return glue
