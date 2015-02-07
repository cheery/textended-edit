from boxmodel import *
import defaultlayout

constructs = globals()

def layout(mapping, env):
    subj = mapping.subj
    listing = []
    for subnode in subj:
        listing.append(hpack(layout2(env, subnode)))
        listing.append(Glue(5))
    return vpack(listing)

def layout2(env, subj):
    if subj.isblank():
        box = hpack(plaintext(env, "___", color=env['blue']))
        box.depth = 2
        box.height = 14
        box.set_subj(subj, 0)
        return [box]
    if subj.issymbol():
        return plaintext(env, subj)
    if isinstance(subj.contents, str):
        if len(subj.label) > 0:
            prefix = env['font'](subj.label, env['fontsize'], color=env['blue'])
            prefix += env['font']('#', env['fontsize'], color=env['pink'])
            postfix = env['font']('#', env['fontsize'], color=env['pink'])
        else:
            prefix = env['font']('#', env['fontsize'], color=env['pink'])
            postfix = env['font']('#', env['fontsize'], color=env['pink'])
        return [hpack(prefix + env['font'](subj, env['fontsize'], color=env['pink']) + postfix)]
    if isinstance(subj.contents, unicode):
        if len(subj.label) > 0:
            prefix = env['font'](subj.label, env['fontsize'], color=env['blue'])
            prefix += env['font']('"', env['fontsize'], color=env['green'])
            postfix = env['font']('"', env['fontsize'], color=env['green'])
        else:
            prefix = env['font']('"', env['fontsize'], color=env['green'])
            postfix = env['font']('"', env['fontsize'], color=env['green'])
        return [hpack(prefix + env['font'](subj, env['fontsize'], color=env['green']) + postfix)]
    name = "layout_" + subj.label.replace('-', '_')
    if name in constructs:
        result = constructs[name](env, subj)
        if result is not None:
            return result
    tokens = []
    tokens.extend(plaintext(env, '(', color=env['gray']))
    tokens.extend(plaintext(env, subj.label, color=env['blue']))
    space = len(subj.label) > 0
    for node in subj:
        if space:
            tokens.extend(plaintext(env, ' '))
        tokens.extend(layout2(env, node))
        space = True
    tokens.extend(plaintext(env, ')', color=env['gray']))
    return hpack(tokens)

def layout_construct(env, subj):
    if len(subj) != 2:
        return
    if not subj[0].issymbol():
        return
    if not subj[1].islist():
        return
    name, rule = subj
    tokens = plaintext(env, name)
    tokens += plaintext(env, " ===", color=env['blue'])
    for node in rule:
        tokens += plaintext(env, " ", color=env['blue'])
        tokens.extend(layout2(env, node))
    return hpack(tokens)

def layout_call(env, subj):
    if len(subj) != 2:
        return
    if not subj[0].issymbol():
        return
    name, rhs = subj
    tokens = plaintext(env, name)
    tokens += plaintext(env, "(", color=env['blue'])
    tokens.extend(layout2(env, rhs))
    tokens += plaintext(env, ")", color=env['blue'])
    return hpack(tokens)

def layout_production_rule(env, subj):
    if len(subj) != 2:
        return
    if not subj[0].islist():
        return
    if not subj[1].islist():
        return
    lhs, rhs = subj

    leftside = []
    for node in lhs:
        if len(leftside) > 0:
            leftside.append(Glue(1))
        leftside.append(hpack(layout2(env, node)))
    rightside = []
    for node in rhs:
        if len(rightside) > 0:
            rightside.append(Glue(1))
        rightside.append(hpack(layout2(env, node)))
    return hpack([vpack_center(leftside)] + plaintext(env, "  --->  ", color=env['blue']) + [vpack_center(rightside)])

def vpack_center(sequence):
    box = vpack(sequence)
    box.height = box.depth = box.vsize * 0.5
    return box

def plaintext(env, text, size=None, color=None):
    size = env['fontsize'] if size is None else size
    color = env['white'] if color is None else color
    return env['font'](text, size, color=color)
