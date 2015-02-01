import layout, font, boxmodel, dom, visual

def link_bridges(primary, layer):
    for node in layer.document.body:
        if node.islist() and node.label == 'reference':
            reference = None
            target = None
            for subnode in node:
                if subnode.isbinary():
                    reference = subnode[:]
                elif subnode.islist():
                    target = subnode
            yield visual.Bridge(layer, reference, target)

def layout(mapping, env):
    node = mapping.subj
    if node.isblank():
        box = boxmodel.hpack(plaintext(env, "___"))
        box.depth = 2
        box.height = 14
        box.set_subj(mapping.subj, 0)
        return [box]
    elif isinstance(node, dom.Symbol):
        sym = env['font'](node, env['fontsize'], color=env['white'])
        if len(node) == 0:
            return [boxmodel.hpack(plaintext(env, "|", color=env['gray']) + sym + plaintext(env, "|", color=env['gray']))]
        else:
            return [boxmodel.hpack(sym)]
    elif isinstance(node.contents, str):
        if len(node.label) > 0:
            prefix = env['font'](node.label, env['fontsize'], color=env['blue'])
            prefix += env['font']('#', env['fontsize'], color=env['pink'])
            postfix = env['font']('#', env['fontsize'], color=env['pink'])
        else:
            prefix = env['font']('#', env['fontsize'], color=env['pink'])
            postfix = env['font']('#', env['fontsize'], color=env['pink'])
        return [boxmodel.hpack(prefix + env['font'](node, env['fontsize'], color=env['pink']) + postfix)]
    elif isinstance(node.contents, unicode):
        if len(node.label) > 0:
            prefix = env['font'](node.label, env['fontsize'], color=env['blue'])
            prefix += env['font']('"', env['fontsize'], color=env['green'])
            postfix = env['font']('"', env['fontsize'], color=env['green'])
        else:
            prefix = env['font']('"', env['fontsize'], color=env['green'])
            postfix = env['font']('"', env['fontsize'], color=env['green'])
        return [boxmodel.hpack(prefix + env['font'](node, env['fontsize'], color=env['green']) + postfix)]
    elif mapping.index is None:
        tokens = []
        for submapping in mapping:
            if submapping.index > 0:
                tokens.append(boxmodel.Glue(4))
            tokens.extend(submapping.update(layout, env))
        return tokens
    else:
        tokens = []
        space = False
        if len(node.label) > 0:
            tokens.append(boxmodel.hpack(env['font'](node.label, env['fontsize'], color=env['blue'])))
            space = True
        for submapping in mapping:
            if space:
                tokens.extend(env['font'](' ', env['fontsize'], color=env['white']))
            tokens.extend(submapping.update(layout, env))
            space = True
        return [lazy_lisp_break(env, tokens, 300)]

def plaintext(env, text, size=None, color=None):
    size = env['fontsize'] if size is None else size
    color = env['white'] if color is None else color
    return env['font'](text, size, color=color)

def lazy_lisp_break(env, tokens, max_width):
    columns = []
    line = []
    width = 0
    tokens = iter(tokens)
    for token in tokens:
        if isinstance(token, (boxmodel.VBox, boxmodel.Padding)) or width + token.width > max_width:
            columns.append(boxmodel.Glue(4))
            columns.append(token)
            break
        else:
            line.append(token)
            width += token.width
    for token in tokens:
        columns.append(boxmodel.Glue(4))
        columns.append(token)
    if len(columns) > 0:
        return boxmodel.vpack([
            boxmodel.hpack(line),
            boxmodel.Padding(
                boxmodel.vpack(columns),
                (10, 0, 0, 0),
                boxmodel.Patch9("assets/border-left-1px.png"),
                color=env['gray'])])
    else:
        line = env['font']('(', env['fontsize'], color=env['gray']) + line + env['font'](')', env['fontsize'], color=env['gray'])
        return boxmodel.hpack(line)
