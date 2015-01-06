import layout, font, boxmodel, dom

sans = font.load('OpenSans.fnt')

def layout_generic(node):
    if not isinstance(node, dom.Literal):
        return sans(node, 12)
    elif isinstance(node.contents, str):
        if len(node.label) > 0:
            prefix = sans(node.label + ':#', 8)
            postfix = sans('#', 8)
        else:
            prefix = sans('#', 8)
            postfix = sans('#', 8)
        return prefix + sans(node, 12) + postfix
    elif isinstance(node.contents, unicode):
        if len(node.label) > 0:
            prefix = sans(node.label + ':"', 8)
            postfix = sans('"', 8)
        else:
            prefix = sans('"', 8)
            postfix = sans('"', 8)
        return prefix + sans(node, 12) + postfix
    elif node.label == 'list':
        hmode = layout.HMode(node)
        hmode.extend(sans('[', 14))
        for i, subnode in enumerate(node):
            if i > 0:
                hmode.append(boxmodel.Glue(8))
            hmode(layout_generic, subnode)
        hmode.extend(sans(']', 14))
        return hmode
    else:
        hmode = layout.HMode(node)
        if len(node.label) > 0:
            hmode.extend(sans(node.label + ':', 8))
        for i, subnode in enumerate(node):
            if i == 1:
                hmode.extend(sans('(', 14))
            if i > 1:
                hmode.append(boxmodel.Glue(8))
            hmode(layout_generic, subnode)
        if len(node) < 2:
            hmode.extend(sans('(', 14))
        hmode.extend(sans(')', 14))
        return hmode

def build_boxmodel(editor):
    body = editor.document.body
    if body.type != 'list':
        return boxmodel.hpack(sans(body, 12))
    mode = layout.VMode(body)
    for i, node in enumerate(body):
        if i > 0:
            mode.append(boxmodel.Glue(8))
        mode(layout_generic, node)
    return mode.freeze()
