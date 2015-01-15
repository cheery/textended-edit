import layout, font, boxmodel, dom
from mapping import Mapping

sans = font.load('OpenSans.fnt')
fontsize = 10
fontsize_small = 6

blue   = 0.5, 0.5, 1.0, 1.0
green  = 1.0, 1.0, 0.0, 1.0
yellow = 1.0, 1.0, 0.0, 1.0
pink   = 1.0, 0.0, 1.0, 1.0
gray   = 0.5, 0.5, 0.5, 1.0

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

def lisp_layout(mapping):
    node = mapping.subj
    if isinstance(node, dom.Symbol):
        return sans(mapping.subj, fontsize)
    elif isinstance(node.contents, str):
        if len(node.label) > 0:
            prefix = sans(node.label, fontsize, color=blue)
            prefix += sans('#', fontsize, color=pink)
            postfix = sans('#', fontsize, color=pink)
        else:
            prefix = sans('#', fontsize, color=pink)
            postfix = sans('#', fontsize, color=pink)
        return prefix + sans(node, fontsize, color=pink) + postfix
    elif isinstance(node.contents, unicode):
        if len(node.label) > 0:
            prefix = sans(node.label, fontsize, color=blue)
            prefix += sans('"', fontsize, color=green)
            postfix = sans('"', fontsize, color=green)
        else:
            prefix = sans('"', fontsize, color=green)
            postfix = sans('"', fontsize, color=green)
        return prefix + sans(node, fontsize, color=green) + postfix
    elif isinstance(node.contents, list):
        tokens = []
        tokens.extend(sans('(', fontsize, color=gray))
        if len(node.label) > 0:
            tokens.extend(sans(node.label, fontsize, color=blue))
        for submapping in mapping:
            if submapping.index > 0 or len(node.label) > 0:
                tokens.extend(sans(' ', fontsize))
            tokens.extend(submapping.apply(lisp_layout))
        tokens.extend(sans(')', fontsize, color=gray))
        width = sum(token.width for token in tokens if token.render > 0)
        if width > 300:
            return [vmode(tokens)]
        else:
            return [boxmodel.hpack(tokens)]

def build_boxmodel(editor):
    editor.mappings.clear()
    mapping = Mapping(editor.mappings, editor.document.body)
    def layout(mapping):
        for submapping in mapping:
            for token in submapping.apply(lisp_layout):
                yield token
    mapping.apply(layout)
    return vmode(mapping.tokens)

def vmode(tokens):
    state = 'vertical'
    hoist = []
    frames = []
    for token in tokens:
        if token.clue == 'horizontal':
            hoist.append(token)
            state = token.clue
        elif token.clue == 'hoist':
            hoist.append(token)
        else:
            if state == 'horizontal':
                frames.append(boxmodel.hpack(hoist))
                hoist = []
            else:
                frames.extend(hoist)
                hoist[:] = ()
            frames.append(token)
            state = 'vertical'
    if state == 'horizontal':
        frames.append(boxmodel.hpack(hoist))
        hoist = []
    else:
        frames.extend(hoist)
        hoist[:] = ()
    return boxmodel.vpack(frames)
