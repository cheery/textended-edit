from boxmodel import *
from schema import Rule, ListRule, modeline, modechange, blankschema, has_modeline
import importlib

def page(workspace, env, subj):
    context = Object(workspace=workspace, env=env, outboxes=[], schema=blankschema, layout=None)
    tokens = []
    if has_modeline(subj):
        configure_schema(context, subj[0])
    for node in subj:
        tokens.extend(layout_element(context, node))
    return vpack(tokens), context.outboxes

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
    return [hpack(tokens)]

def plaintext(env, text, fontsize=None, color=None):
    return env.font(text,
        env.fontsize if fontsize is None else fontsize,
        color = env.white if color is None else color)

class Object(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])
