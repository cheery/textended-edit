from minitex import *
from layout import notation

def layout_import_from(lhs, rhs):
    boxes = []
    for alias in rhs:
        boxes.append(notation(' '))
        boxes.append(alias)
    return codeline([
        notation('import '),
        lhs,
        notation(' from')] + boxes)

def layout_let(lhs, rhs):
    return codeline([lhs, notation(" = "), rhs])

def layout_function(args, body):
    boxes = []
    boxes.append(notation('('))
    space = False
    for arg in args:
        if space:
            boxes.append(notation(', '))
        boxes.append(arg)
        space = True
    boxes.append(notation('):'))
    for stmt in body:
        boxes.append(nl)
        boxes.append(stmt)
    return codeline(boxes)

def layout_return(expr):
    return codeline([notation('return '), expr])

def layout_call(callee, args):
    boxes = [callee, notation('('), nl]
    space = False
    for arg in args:
        if space:
            boxes.append(notation(', '))
            boxes.append(nl)
        boxes.append(arg)
        space = True
    boxes.append(notation(')'))
    return codeline(boxes)

def layout_list(*exprs):
    boxes = [notation('['), nl]
    space = False
    for expr in exprs:
        if space:
            boxes.append(notation(', '))
            boxes.append(nl)
        boxes.append(expr)
        space = True
    boxes.append(notation(']'))
    return codeline(boxes)
