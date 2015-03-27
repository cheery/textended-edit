from boxmodel import *
from dom import TextCell, ListCell
from minitex import *
#from schema import Rule, Star, ListRule, modeline, modechange, blankschema, has_modeline
#import dom
#import importlib
#
def page(document, options):
    env = Environ.root(options)
    box = toplevel(layout_document(document), env, dict(page_width=300, indent=40))#dict(page_width=width-20, line_break=line_break))
    return box, []

def layout_document(document):
    lines = []
    for cell in document.body:
        lines.append(layout_cell(cell))
        lines.append(brk)
    if document.body.is_external():
        lines.append(external_marker(document.body))
    return lines
                
def external_marker(cell):
    def _fold(env):
        yield hpack(env.font("._.", env.font_size, color=env.color_empty)).set_subj(cell, 0)
    return _fold

def blank_marker(cell):
    def _fold(env):
        yield hpack(env.font("_", env.font_size, color=env.color_empty)).set_subj(cell, 0)
    return _fold

def string_wrap(cell):
    def _fold(env):
        pre = env.font('"', env.font_size, color=env.color_string)
        pos = env.font('"', env.font_size, color=env.color_string)
        return pre + env.font(cell, env.font_size, color=env.color_string) + pos
    return _fold

def notation(text):
    def _fold(env):
        yield hpack(env.font(text, env.font_size, color=env.color_notation))
    return _fold

def layout_cell(cell):
    if isinstance(cell, TextCell):
        if cell.is_blank() and cell.symbol:
            return blank_marker(cell)
        if cell.symbol:
            return cell
        return string_wrap(cell)
    if cell.is_external():
        return external_marker(cell)
    row = []
    row.append(notation("["))
    spac = False
    if len(cell.label) > 0:
        row.append(notation(cell.label))
        spac = True
    for subcell in cell:
        if spac:
            row.append(" ")
        row.append(layout_cell(subcell))
        spac = True
    row.append(notation("]"))
    return scope(row)
#def layout_cell(cell, options):
#    if isinstance(cell, TextCell):
#        if cell.is_blank() and cell.symbol:
#            return hpack(plain("_", options, 'color_empty')).set_subj(cell, 0)
#        if cell.symbol:
#            return hpack(plain(cell, options))
#    if cell.is_external():
#        return hpack(plain("._.", options, 'color_empty')).set_subj(cell, 0)
#    boxes = []
#    boxes.extend(plain("[", options, 'color_notation'))
#    boxes.extend(plain(cell.label, options, 'color_notation' if cell.rule else 'color_notation_error'))
#    for subcell in cell:
#        boxes.extend(plain(" ", options, 'color_notation'))
#        boxes.append(layout_cell(subcell, options))
#    boxes.extend(plain("]", options, 'color_notation'))
#    return hpack(boxes)
#
#def plain(cell, options, color='white'):
#    return options['font'](cell, options['font_size'], color=options[color])


#def page(workspace, env, subj):
#    context = Object(workspace=workspace, env=env, outboxes=[], schema=blankschema, layout=None)
#    tokens = []
#    if has_modeline(subj):
#        configure_schema(context, subj[0])
#    for node in subj:
#        tokens.extend(layout_element(context, node))
#        tokens.append(separator(context.env))
#    tokens.extend(sentinel(context.env, subj))
#    return packlines(tokens, env.width), context.outboxes
#
#def configure_schema(context, modeline):
#    schema_name = modeline[0][:]
#    if schema_name == '':
#        return blankschema
#    context.schema = context.workspace.get_schema(schema_name)
#    try:
#        context.layout = importlib.import_module("layouts." + schema_name)
#    except ImportError:
#        context.layout = None
#
#def layout_element(context, subj):
#    def _layout(slot, subj):
#        result = context.schema.recognize(subj)
#        if result == modeline:
#            return layout_modeline(context, subj)
#        elif isinstance(slot, Star):
#            return list(sentinel(context.env, subj))
#        elif isinstance(result, ListRule):
#            name = result.label.replace('-', '_')
#            if hasattr(context.layout, name):
#                return getattr(context.layout, name)(context, result.build(_layout, subj))
#            tokens = plaintext(context.env, subj.label, color=context.env.blue)
#            for subnode in subj:
#                tokens.append(Glue(2))
#                tokens.extend(_layout(None, subnode))
#            return vskip([hpack(tokens)])
#        elif isinstance(result, Rule):
#            name = result.label.replace('-', '_')
#            if hasattr(context.layout, name):
#                return getattr(context.layout, name)(context, subj)
#            return [hpack(plaintext(context.env, "Rule:" + result.label))]
#        elif result in ('symbol', 'blank'):
#            return plaintext(context.env, subj)
#        elif result == 'list' and subj.label == '@':
#            index = len(context.outboxes)
#            tokens = []
#            for subnode in subj:
#                tokens.extend(_layout(None, subnode))
#                tokens.append(separator(context.env))
#            outbox = Padding(packlines(tokens, context.env.width), (4, 4, 4, 4), Patch9("assets/border-1px.png"))
#            anchor = ImageBox(10, 10, 2, None, context.env.white)
#            context.outboxes.insert(index, (anchor, outbox))
#            return [anchor]
#        elif result == 'list':
#            pre = plaintext(context.env, '{ ', color=context.env.blue)
#            pos = plaintext(context.env, ' }', color=context.env.blue)
#            tokens = []
#            for subnode in subj:
#                tokens.append(hpack(_layout(None, subnode)))
#                tokens.append(separator(context.env))
#            tokens.extend(sentinel(context.env, subj))
#            return pre + tokens + pos
#        elif result == 'string':
#            pre = plaintext(context.env, '"', color=context.env.yellow)
#            pos = plaintext(context.env, '"', color=context.env.yellow)
#            return [hpack(pre + plaintext(context.env, subj, color=context.env.yellow) + pos)]
#        else:
#            return [hpack(plaintext(context.env, result + ":" + subj.label))]
#    return _layout(None, subj)
#
#def layout_modeline(context, modeline):
#    tokens = []
#    tokens.extend(plaintext(context.env, "##", color=context.env.blue))
#    for sym in modeline:
#        tokens.extend(plaintext(context.env, " "))
#        tokens.extend(plaintext(context.env, sym))
#    line = hpack(tokens)
#    line.hint = {'vskip': True}
#    return [line]
#
#def plaintext(env, text, fontsize=None, color=None):
#    if isinstance(text, dom.Symbol) and len(text) == 0:
#        box = hpack(plaintext(env, "___"))
#        box.set_subj(text, 0)
#        return [box]
#    return env.font(text,
#        env.fontsize if fontsize is None else fontsize,
#        color = env.white if color is None else color)
#
#def sentinel(env, subj):
#    if len(subj) == 0:
#        yield ImageBox(10, 10, 5, None, env.gray).set_subj(subj, 0)
#        yield Glue(2)
#
#def vskip(boxes):
#    for box in boxes:
#        if box.hint is None:
#            box.hint = {'vskip': True}
#        else:
#            box.hint.update({'vskip': True})
#    return boxes
#
#def packlines(tokens, width):
#    out = []
#    line = []
#    total_width = 0
#    greedy_cutpoint = -1
#    for token in tokens:
#        if (token.vsize > 20 and not isinstance(token, Glue)) or token.get_hint('vskip', False):
#            if len(line) > 0:
#                out.append(hpack(line))
#            out.append(token)
#            line = []
#            greedy_cutpoint = -1
#            total_width = 0
#        else:
#            if token.get_hint('break', False):
#                if len(line) == 0:
#                    continue
#                greedy_cutpoint = len(line)
#            line.append(token)
#            total_width += token.width
#            if total_width > width and greedy_cutpoint >= 0:
#                out.append(hpack(line[:greedy_cutpoint+1]))
#                line = line[greedy_cutpoint+1:]
#                total_width = sum(item.width for item in line)
#    if len(line) > 0:
#        out.append(hpack(line))
#    return vpack(out)
#
#class Object(object):
#    def __init__(self, **kw):
#        for k in kw:
#            setattr(self, k, kw[k])
#
#def separator(env):
#    glue = Glue(4)
#    glue.hint = {'break': True}
#    return glue
