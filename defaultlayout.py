import layout, font, boxmodel, dom

sans = font.load('OpenSans.fnt')
fontsize = 10
fontsize_small = 6

white  = 1.0, 1.0, 1.0, 1.0
blue   = 0.5, 0.5, 1.0, 1.0
green  = 1.0, 1.0, 0.0, 1.0
yellow = 1.0, 1.0, 0.0, 1.0
pink   = 1.0, 0.0, 1.0, 1.0
gray   = 0.5, 0.5, 0.5, 1.0

def build(mapping):
    node = mapping.subj
    if isinstance(node, dom.Symbol):
        return [boxmodel.hpack(sans(node, fontsize, color=white))]
    if isinstance(node.contents, str):
        if len(node.label) > 0:
            prefix = sans(node.label, fontsize, color=blue)
            prefix += sans('#', fontsize, color=pink)
            postfix = sans('#', fontsize, color=pink)
        else:
            prefix = sans('#', fontsize, color=pink)
            postfix = sans('#', fontsize, color=pink)
        return [boxmodel.hpack(prefix + sans(node, fontsize, color=pink) + postfix)]
    elif isinstance(node.contents, unicode):
        if len(node.label) > 0:
            prefix = sans(node.label, fontsize, color=blue)
            prefix += sans('"', fontsize, color=green)
            postfix = sans('"', fontsize, color=green)
        else:
            prefix = sans('"', fontsize, color=green)
            postfix = sans('"', fontsize, color=green)
        return [boxmodel.hpack(prefix + sans(node, fontsize, color=green) + postfix)]
    elif mapping.index is None:
        tokens = []
        for i, subtokens in enumerate(mapping):
            if i > 0:
                tokens.append(boxmodel.Glue(4))
            tokens.extend(subtokens)
        return tokens
    else:
        tokens = []
        space = False
        if len(node.label) > 0:
            tokens.append(boxmodel.hpack(sans(node.label, fontsize, color=blue)))
            space = True
        for subtokens in mapping:
            if space:
                tokens.extend(sans(' ', fontsize, color=white))
            tokens.extend(subtokens)
            space = True
        return [lazy_lisp_break(tokens, 300)]

def lazy_lisp_break(tokens, max_width):
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
                color=gray)])
    else:
        line = sans('(', fontsize, color=gray) + line + sans(')', fontsize, color=gray)
        return boxmodel.hpack(line)
