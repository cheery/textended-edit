import layout, font, boxmodel, dom

sans = font.load('OpenSans.fnt')

def layout_generic(node):
    if not isinstance(node, dom.Literal):
        return sans(node, 8)
    elif isinstance(node.contents, str):
        if len(node.label) > 0:
            prefix = sans(node.label + ':#', 8)
            postfix = sans('#', 8)
        else:
            prefix = sans('#', 8)
            postfix = sans('#', 8)
        return prefix + sans(node, 8) + postfix
    elif isinstance(node.contents, unicode):
        if len(node.label) > 0:
            prefix = sans(node.label + ':"', 8)
            postfix = sans('"', 8)
        else:
            prefix = sans('"', 8)
            postfix = sans('"', 8)
        return prefix + sans(node, 8) + postfix
    else:
        hmode = layout.HMode(node)
        if len(node.label) > 0:
            hmode.extend(sans(node.label + ':', 8))
        hmode.extend(sans('[', 8))
        for i, subnode in enumerate(node):
            if i > 0:
                hmode.append(boxmodel.Glue(8))
            hmode(layout_generic, subnode)
        hmode.extend(sans(']', 8))
        return hmode
#    else:
#        hmode = layout.HMode(node)
#        if len(node.label) > 0:
#            hmode.extend(sans(node.label + ':', 8))
#        for i, subnode in enumerate(node):
#            if i == 1:
#                hmode.extend(sans('(', 14))
#            if i > 1:
#                hmode.append(boxmodel.Glue(8))
#            hmode(layout_generic, subnode)
#        if len(node) < 2:
#            hmode.extend(sans('(', 14))
#        hmode.extend(sans(')', 14))
#        return hmode

def layout_python(node):
    if check_literal(node, 'import', 'list'):
        mode = layout.HMode(node)
        mode.extend(sans('import', 8))
        for subnode in node:
            mode.append(boxmodel.Glue(8))
            mode(layout_python, subnode)
        return mode
    if check_literal(node, 'attr', 'list') and len(node) == 2:
        mode = layout.HMode(node)
        mode(layout_python, node[0])
        mode.extend(sans(".", 8))
        mode(layout_python, node[1])
        return mode
    if check_literal(node, 'assign', 'list'):
        mode = layout.HMode(node)
        for i, node in enumerate(node):
            if i > 0:
                mode.extend(sans(" = ", 8))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'if', 'list'):
        mode = layout.VMode(node)
        mode.indent = 10
        mode.append(boxmodel.hpack(sans("if", 8)))
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(8))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'def', 'list'):
        mode = layout.VMode(node)
        mode.indent = 10
        mode.append(boxmodel.hpack(sans("def", 8)))
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(8))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'cond', 'list'):
        mode = layout.VMode(node)
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.hpack(sans('else', 8)))
            mode(layout_python, node)
        return mode
    if check_literal(node, "", 'list') and node.parent.label == 'cond':
        mode = layout.VMode(node)
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(8))
            mode(layout_python, node)
        return mode
    if check_literal(node, "", 'list'):
        hmode = layout.HMode(node)
        for i, subnode in enumerate(node):
            if i == 1:
                hmode.extend(sans('(', 8))
            if i > 1:
                hmode.extend(sans(',', 8))
                hmode.append(boxmodel.Glue(8))
            hmode(layout_python, subnode)
        if len(node) < 1:
            hmode.extend(sans('(', 8))
        hmode.extend(sans(')', 8))
        return hmode
    return layout_generic(node)

def check_literal(node, label, type):
    return isinstance(node, dom.Literal) and node.label == label and node.type == type

def build_boxmodel(editor):
    body = editor.document.body
    layoutfn = layout_generic
    for node in body:
        if isinstance(node, dom.Literal) and node.label == 'language' and node[:] == "python":
            layoutfn = layout_python

    if body.type != 'list':
        return boxmodel.hpack(sans(body, 8))
    mode = layout.VMode(body)
    for i, node in enumerate(body):
        if i > 0:
            mode.append(boxmodel.Glue(8))
        mode(layoutfn, node)
    return mode.freeze()
