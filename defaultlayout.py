import layout, font, boxmodel, dom

sans = font.load('OpenSans.fnt')
fontsize = 10
fontsize_small = 6

def layout_generic(node):
    if not isinstance(node, dom.Literal):
        return sans(node, fontsize)
    elif isinstance(node.contents, str):
        if len(node.label) > 0:
            prefix = sans(node.label + ':#', fontsize_small)
            postfix = sans('#', fontsize_small)
        else:
            prefix = sans('#', fontsize_small)
            postfix = sans('#', fontsize_small)
        return prefix + sans(node, fontsize_small) + postfix
    elif isinstance(node.contents, unicode):
        if len(node.label) > 0:
            prefix = sans(node.label + ':"', fontsize_small)
            postfix = sans('"', fontsize_small)
        else:
            prefix = sans('"', fontsize_small)
            postfix = sans('"', fontsize_small)
        return prefix + sans(node, fontsize_small) + postfix
    else:
        hmode = layout.HMode(node)
        if len(node.label) > 0:
            hmode.extend(sans(node.label + ':', fontsize_small))
        hmode.extend(sans('[', fontsize_small))
        for i, subnode in enumerate(node):
            if i > 0:
                hmode.append(boxmodel.Glue(fontsize_small))
            hmode(layout_generic, subnode)
        hmode.extend(sans(']', fontsize_small))
        return hmode

def layout_python(node):
    if check_literal(node, 'import', 'list'):
        mode = layout.HMode(node)
        mode.extend(sans('import', fontsize))
        for i, subnode in enumerate(node):
            if i > 0:
                mode.extend(sans(', ', fontsize))
            else:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, subnode)
        return mode
    if check_literal(node, 'attr', 'list') and len(node) == 2:
        mode = layout.HMode(node)
        mode(layout_python, node[0])
        mode.extend(sans(".", fontsize))
        mode(layout_python, node[1])
        return mode
    if check_literal(node, 'assign', 'list'):
        mode = layout.HMode(node)
        for i, node in enumerate(node):
            if i > 0:
                mode.extend(sans(" = ", fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'return', 'list'):
        mode = layout.HMode(node)
        mode.extend(sans("return", fontsize))
        for i, node in enumerate(node):
            if i > 0:
                mode.extend(sans(", ", fontsize))
            else:
                mode.extend(sans(" ", fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'binop', 'list'):
        mode = layout.HMode(node)
        for i, node in enumerate(node):
            if i > 0:
                mode.extend(sans(" ", fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'unaryop', 'list'):
        mode = layout.HMode(node)
        for i, node in enumerate(node):
            mode(layout_python, node)
        return mode
    if check_literal(node, 'if', 'list'):
        mode = layout.VMode(node)
        mode.indent = 10
        mode.append(boxmodel.hpack(sans("if", fontsize)))
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'def', 'list'):
        mode = layout.VMode(node)
        mode.indent = 10
        mode.append(boxmodel.hpack(sans("def", fontsize)))
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'cond', 'list'):
        mode = layout.VMode(node)
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.hpack(sans('else', fontsize)))
            mode(layout_python, node)
        return mode
    if check_literal(node, "", 'list') and node.parent.label == 'cond':
        mode = layout.VMode(node)
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, "", 'list'):
        hmode = layout.HMode(node)
        for i, subnode in enumerate(node):
            if i == 1:
                hmode.extend(sans('(', fontsize))
            if i > 1:
                hmode.extend(sans(',', fontsize))
                hmode.append(boxmodel.Glue(fontsize))
            hmode(layout_python, subnode)
        if len(node) < 1:
            hmode.extend(sans('(', fontsize))
        hmode.extend(sans(')', fontsize))
        return hmode
    elif check_literal(node, "", 'string'):
        prefix = sans('"', fontsize)
        postfix = sans('"', fontsize)
        return prefix + sans(node, fontsize) + postfix
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
        return boxmodel.hpack(sans(body, fontsize))
    mode = layout.VMode(body)
    for i, node in enumerate(body):
        if i > 0:
            mode.append(boxmodel.Glue(fontsize))
        mode(layoutfn, node)
    return mode.freeze()
