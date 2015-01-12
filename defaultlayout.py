import layout, font, boxmodel, dom

sans = font.load('OpenSans.fnt')
fontsize = 10
fontsize_small = 6

blue   = 0.5, 0.5, 1.0, 1.0
green  = 1.0, 1.0, 0.0, 1.0
yellow = 1.0, 1.0, 0.0, 1.0
pink   = 1.0, 0.0, 1.0, 1.0

def layout_generic(mapping):
    node = mapping.subj
    if not isinstance(node, dom.Literal):
        return sans(node, fontsize)
    elif isinstance(node.contents, str):
        if len(node.label) > 0:
            prefix = sans(node.label, fontsize_small, color=blue)
            prefix += sans('#', fontsize_small, color=pink)
            postfix = sans('#', fontsize_small, color=pink)
        else:
            prefix = sans('#', fontsize_small, color=pink)
            postfix = sans('#', fontsize_small, color=pink)
        return prefix + sans(node, fontsize_small, color=pink) + postfix
    elif isinstance(node.contents, unicode):
        if len(node.label) > 0:
            prefix = sans(node.label, fontsize_small, color=blue)
            prefix += sans('"', fontsize_small, color=green)
            postfix = sans('"', fontsize_small, color=green)
        else:
            prefix = sans('"', fontsize_small, color=green)
            postfix = sans('"', fontsize_small, color=green)
        return prefix + sans(node, fontsize_small, color=green) + postfix
    else:
        hmode = layout.HMode(mapping)
        hmode.extend(sans('[', fontsize))
        if len(node.label) > 0:
            hmode.extend(sans(node.label, fontsize, color=blue))
            hmode.append(boxmodel.Glue(fontsize))
        for i, subnode in enumerate(node):
            if i > 0:
                hmode.append(boxmodel.Glue(fontsize))
            hmode(layout_generic, subnode)
        hmode.extend(sans(']', fontsize))
        return hmode

def layout_python(mapping):
    node = mapping.subj
    if check_literal(node, 'import', 'list'):
        mode = layout.HMode(mapping)
        mode.extend(sans('import', fontsize))
        for i, subnode in enumerate(node):
            if i > 0:
                mode.extend(sans(', ', fontsize))
            else:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, subnode)
        return mode
    if check_literal(node, 'attr', 'list') and len(node) == 2:
        mode = layout.HMode(mapping)
        mode(layout_python, node[0])
        mode.extend(sans(".", fontsize))
        mode(layout_python, node[1])
        return mode
    if check_literal(node, 'assign', 'list'):
        mode = layout.HMode(mapping)
        for i, node in enumerate(node):
            if i > 0:
                mode.extend(sans(" = ", fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'return', 'list'):
        mode = layout.HMode(mapping)
        mode.extend(sans("return", fontsize))
        for i, node in enumerate(node):
            if i > 0:
                mode.extend(sans(", ", fontsize))
            else:
                mode.extend(sans(" ", fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'binop', 'list'):
        mode = layout.HMode(mapping)
        for i, node in enumerate(node):
            if i > 0:
                mode.extend(sans(" ", fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'unaryop', 'list'):
        mode = layout.HMode(mapping)
        for i, node in enumerate(node):
            mode(layout_python, node)
        return mode
    if check_literal(node, 'if', 'list'):
        mode = layout.VMode(mapping)
        mode.indent = 10
        mode.append(boxmodel.hpack(sans("if", fontsize)))
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'def', 'list'):
        mode = layout.VMode(mapping)
        mode.indent = 10
        mode.append(boxmodel.hpack(sans("def", fontsize)))
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, 'cond', 'list'):
        mode = layout.VMode(mapping)
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.hpack(sans('else', fontsize)))
            mode(layout_python, node)
        return mode
    if check_literal(node, "", 'list') and node.parent.label == 'cond':
        mode = layout.VMode(mapping)
        for i, node in enumerate(node):
            if i > 0:
                mode.append(boxmodel.Glue(fontsize))
            mode(layout_python, node)
        return mode
    if check_literal(node, "", 'list'):
        hmode = layout.HMode(mapping)
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
    return layout_generic(mapping)

def check_literal(node, label, type):
    return isinstance(node, dom.Literal) and node.label == label and node.type == type

class Mapping(object):
    __slots__ = ['frames', 'subj', 'obj']
    def __init__(self, frames, subj):
        self.frames = frames
        self.subj = subj
        self.obj = None

    def submapping(self, node):
        self.frames[node] = mapping = Mapping(self.frames, node)
        return mapping

def build_boxmodel(editor):
    body = editor.document.body
    layoutfn = layout_generic
    for node in body:
        if isinstance(node, dom.Literal) and node.label == 'language' and node[:] == "python":
            layoutfn = layout_python

    if body.type != 'list':
        return boxmodel.hpack(sans(body, fontsize))

    editor.frames[body] = mapping = Mapping(editor.frames, body)

    mode = layout.VMode(mapping)
    for i, node in enumerate(body):
        if i > 0:
            mode.append(boxmodel.Glue(fontsize))
        mode(layoutfn, node)
    return mode.freeze()
