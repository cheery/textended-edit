from dom import Cell, TextCell, ListCell
from grammar import modeline, Star, Plus
from position import Position
import sys
import traceback

def interpret(visual, keyboard):
    for key, mod, text in keyboard:
        head, tail = visual.head, visual.tail
        try:
            if key == 'escape':
                sys.exit(0)
            elif key == 'f2':
                body = visual.head.cell.document.body
                if len(body) > 0 and modeline.validate(body[0]):
                    visual.setpos(Position.bottom(body[0]))
                else:
                    blank = modeline.blank()
                    body.put(0, [blank])
                    visual.setpos(Position.bottom(blank))
            elif key == 'f4':
                for cell in visual.head.cell.hierarchy:
                    print cell,
                print
                for cell in visual.head.cell.hierarchy:
                    print cell.rule,
                print
                for cell in visual.head.cell.hierarchy:
                    print cell.grammar,
                print
            elif key == unichr(167):
                start_completion(visual)
            elif key == 'tab':
                if 'shift' in mod:
                    start_expansion(visual)
                else:
                    start_composition(visual)
            elif key == 'x' and 'ctrl' in mod:
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(position)
                position.cell.document.workspace.clipboard = clipboard
            elif key == 'v' and 'ctrl' in mod:
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(put(position, clipboard)[1])
            elif key == 'z' and 'ctrl' in mod:
                visual.head, visual.tail = visual.document.undo()
            elif key == 'left':
                head = visual.head
                if head.on_left_boundary:
                    head = Position.bottom(head.cell.previous_external) 
                else:
                    head -= 1
                tail = visual.tail if 'shift' in mod else head 
                visual.setpos(head, tail)
            elif key == 'right':
                head = visual.head
                if head.on_right_boundary:
                    head = Position.top(head.cell.next_external) 
                else:
                    head += 1
                tail = visual.tail if 'shift' in mod else head 
                visual.setpos(head, tail)
            elif key == 'backspace':
                if visual.head == visual.tail:
                    if visual.head.on_left_boundary:
                        visual.setpos(join_left(visual.head))
                    else:
                        visual.setpos(collapse(visual.head-1, visual.tail)[0])
                else:
                    visual.setpos(collapse(visual.head, visual.tail)[0])
            elif key == 'delete':
                if visual.head == visual.tail:
                    if visual.head.on_right_boundary:
                        visual.setpos(join_right(visual.head))
                    else:
                        visual.setpos(collapse(visual.head, visual.tail+1)[0])
                else:
                    visual.setpos(collapse(visual.head, visual.tail)[0])
            elif key == 'return':
                position, clipboard = collapse(visual.head, visual.tail)
                if 'shift' in mod:
                    visual.setpos(fall_left(position))
                else:
                    visual.setpos(fall_right(position))
            elif text == ' ':
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(position)
                if not isinstance(clipboard, list):
                    if 'shift' in mod:
                        visual.setpos(split_left(visual.head))
                    else:
                        visual.setpos(split_right(visual.head))
            elif text == '"':
                position, clipboard = collapse(visual.head, visual.tail)
                string = TextCell(u"", symbol=False)
                visual.setpos(put(position, [string])[1])
            elif text is not None:
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(put(position, text)[1])
            else:
                print key, mod, text
        except Exception:
            print "Error during pressing:", key, mod, text
            traceback.print_exc()
            visual.document.rollback()
            visual.head = head
            visual.tail = tail
        else:
            visual.document.commit(head, tail)

def start_completion(visual):
    head = visual.head
    assert head.cell.symbol
    result = []
    query = head.cell[:]
    for rule in head.cell.grammar.rules.values():
        if rule.label.startswith(query):
            result.append(rule)
    result.sort(key=lambda rule: rule.label)
    block = result[0].blank()
    replace(head.cell, block)
    visual.setpos(Position.top(block))
# def completion(visual):
#     workspace = visual.workspace
#     head = visual.head
#     if visual.chain[0] == 'completion':
#         _, block, result, index = visual.chain
#         new_block = result[index].blank()
#         Position(block, 0).replace([new_block])
#         visual.setpos(
#             Position.top(new_block),
#             chain = ('completion',
#                 new_block,
#                 result,
#                 (index + 1) % len(result)))
#     elif head.subj.issymbol():
#         result = []
#         active = workspace.active_schema(head.subj)
#         name = head.subj[:]
#         for rule in active.rules:
#             if rule.startswith(name):
#                 result.append(active.rules[rule])
#         block = result[0].blank()
#         head.replace([block])
#         visual.setpos(
#             Position.top(block),
#             chain = ('completion',
#                 block,
#                 result,
#                 1 % len(result)))
#     else:
#         raise Exception("not implemented")


import parsing
reload(parsing)
def start_composition(visual):
    cell = visual.head.cell
    while cell.label != '@':
        cell = cell.parent
        if cell is None:
            raise Exception("not implemented")
    context = cell.context
    assert context
    result = iter(parsing.parse(cell.copy(), context.rules)).next()
    new_block = result.wrap()
    replace(cell, new_block)
    visual.setpos(Position.bottom(new_block))

# def composition(visual):
#     if visual.chain[0] == 'composition':
#         _, block, result, repeat = visual.chain
#         try:
#             new_block = result.next().build()
#             Position(block, 0).replace([new_block])
#             visual.setpos(
#                 Position.bottom(new_block),
#                 chain = ('composition', new_block, result, repeat))
#         except StopIteration:
#             visual.setpos(
#                 visual.head, visual.tail,
#                 chain = ('composition', block, repeat(), repeat))
#             return composition(visual)
#     else:
#         subj = visual.head.subj
#         while subj.label != '@':
#             subj = subj.parent
#             if subj is None:
#                 raise Exception("not implemented")
#         active = visual.workspace.active_schema(subj)
#         ctx = visual.workspace.active_schema(subj).recognize_in_context(subj)
#         assert isinstance(ctx, Context), ctx
#         repeat = lambda: iter(parsing.parse(subj.copy(), ctx.all_valid_rules))
#         result = repeat()
#         new_block = result.next().build()
#         Position(subj, 0).replace([new_block])
#         visual.setpos(
#             Position.bottom(new_block),
#             chain = ('composition', new_block, result, repeat))

def start_expansion(visual):
    # slightly incorrect, should find the position where expansion is allowable.
    above = visual.head.above
    forest = above.cell.drop(above.index, above.index+1)
    expansion = ListCell(u"@", forest)
    above.cell.put(above.index, [expansion])
    visual.setpos(Position(forest[0], visual.head.index))

def collapse(head, tail):
    if head.cell is tail.cell:
        start = min(head.index, tail.index)
        stop = max(head.index, tail.index)
        return head, head.cell.drop(start, stop)
    common, left, right = head.cell.order(tail.cell)
    g0 = fault_line(common, left, Cell.is_leftmost)
    g1 = fault_line(common, right, Cell.is_rightmost)
    i0 = g0.pop(0)
    i1 = g1.pop(0)
    while len(g0) == len(g1) == 0 and i0 == 0 and i1 == len(common)-1 and common.parent and len(common.label) > 0:
        i0 = i1 = common.parent.index(common)
        common = common.parent
    position, dropped = collapse_range(common, i0, i1+1)
    if len(dropped) == 1:
        return position, dropped
    else:
        leftbound = dropped.pop(0)
        rightbound = dropped.pop(-1)
        prefix = []
        for i in g0:
            sequence = leftbound.dissolve()
            prefix = prefix + sequence[:i]
            leftbound = sequence[i]
            dropped = sequence[i+1:] + dropped
        dropped = [leftbound] + dropped
        postfix = []
        for i in g1:
            sequence = rightbound.dissolve()
            dropped = dropped + sequence[:i]
            rightbound = sequence[i]
            postfix = sequence[i+1:] + postfix
        dropped = dropped + [rightbound]
        new_position = Position(TextCell(u""), 0)
        put(position, trim(prefix + [new_position.cell] + postfix, []))
        return new_position, dropped

def collapse_range(cell, start, stop):
    rule = cell.rule
    dropped = cell.drop(start, stop)
    placeholder = Position(TextCell(u""), 0)
    cell.put(start, [placeholder.cell])
    if rule and not rule.validate(cell):
        cell = carve_turnip(cell)
        placeholder = Position(cell[start], 0)
    return placeholder, dropped

def fault_line(target, cell, cond):
    result = []
    while cond(cell) and cell.parent != target:
        cell = cell.parent
    while cell != target:
        result.append(cell.parent.index(cell))
        cell = cell.parent
    result.reverse()
    return result

def fall_left(position):
    data = position.cell.drop(0, position.index)
    cell = position.cell
    position = position.above
    while True:
        if cell.is_blank() and can_carve(position.cell) and position.above:
            position.cell.drop(position.index, position.index+1)
        elif can_insert(position.cell):
            return put(insert_blank(position), data)[1]
        elif not position.on_left_boundary:
            pos = climb_left(position.cell[position.index-1], None)
            if pos:
                return put(insert_blank(pos), data)[1]
        cell = position.cell
        position = position.above

def fall_right(position):
    data = position.cell.drop(position.index, len(position.cell))
    cell = position.cell
    position = position.above+1
    while True:
        if cell.is_blank() and can_carve(position.cell) and position.above:
            position.cell.drop(position.index-1, position.index)
        elif can_insert(position.cell):
            return put(insert_blank(position), data)[0]
        elif not position.on_right_boundary:
            pos = climb_right(position.cell[position.index], None)
            if pos:
                return put(insert_blank(pos), data)[0]
        cell = position.cell
        position = position.above+1

def join_left(position):
    lhs = Position.bottom(position.cell.previous_external)
    rhs = carve(position)
    return put(lhs, rhs[:])[0]

def join_right(position):
    rhs = Position.top(position.cell.next_external)
    lhs = carve(position)
    return put(rhs, lhs[:])[1]

def carve(position):
    above = position.above
    if can_carve(above.cell):
        cell = above.cell.drop(above.index, above.index+1)[0]
        return cell
    else:
        cell = above.cell.drop(above.index, above.index+1)[0]
        carve_turnip(above.cell)
        return cell

def can_carve(cell):
    rule = cell.rule
    if isinstance(rule, Star):
        return True
    if isinstance(rule, Plus) and len(cell) > 1:
        return True
    if cell.parent is None:
        return True

def carve_turnip(cell):
    parent = cell.parent
    index = parent.index(cell)
    cell = parent.drop(index, index+1)[0]
    new_cell = ListCell(u"@", trim(cell.dissolve(), []))
    parent.put(index, [new_cell])
    return new_cell

def trim(forest, result):
    for cell in forest:
        if isinstance(cell, ListCell) and len(cell.label) == 0:
            trim(cell.dissolve(), result)
        else:
            result.append(cell)
    return result

def split_left(position):
    data = position.cell.drop(0, position.index)
    position = position.above
    while True:
        if can_insert(position.cell):
            return put(insert_blank(position), data)[1]
        elif not position.on_left_boundary:
            position = climb_left(position.cell[position.index-1], position)
            return put(insert_blank(position), data)[1]
        else:
            position = position.above

def split_right(position):
    data = position.cell.drop(position.index, len(position.cell))
    position = position.above+1
    while True:
        if can_insert(position.cell):
            return put(insert_blank(position), data)[0]
        elif not position.on_right_boundary:
            position = climb_right(position.cell[position.index], position)
            return put(insert_blank(position), data)[0]
        else:
            position = position.above+1

def climb_left(cell, otherwise):
    if can_insert(cell):
        return Position(cell, len(cell))
    elif not cell.is_external():
        return climb_right(cell[len(cell)-1], otherwise)
    else:
        return otherwise

def climb_right(cell, otherwise):
    if can_insert(cell):
        return Position(cell, 0)
    elif not cell.is_external():
        return climb_right(cell[0], otherwise)
    else:
        return otherwise

def can_insert(cell):
    rule = cell.rule
    if isinstance(rule, (Star, Plus)):
        return True
    if cell.parent is None:
        return True

def insert_blank(position):
    blank = TextCell(u"")
    if can_insert(position.cell):
        position.cell.put(position.index, [blank])
    else:
        cell = carve_turnip(position.cell)
        cell.put(position.index, [blank])
    return Position.top(blank)

def put(position, data):
    if isinstance(data, list):
        if len(data) == 1:
            return putcell(position, data[0])
        else:
            return putforest(position, data)
    elif isinstance(position.cell, TextCell):
        return puttext(position, data)
    elif position.cell.is_external():
        blank = TextCell(u"")
        position.cell.put(0, [blank])
        return put(Position.bottom(blank), data)
    else:
        raise Exception("bad put")

def putcell(position, cell):
    if position.cell.is_blank():
        context = position.cell.context
        if context:
            if context.match(cell):
                replace(position.cell, cell)
            else:
                replace(position.cell, ListCell(u"@", [cell]))
            return Position.top(cell), Position.bottom(cell)
        else:
            replace(position.cell, cell)
            return Position.top(cell), Position.bottom(cell)
    else:
        raise Exception("not implemented")

def putforest(position, data):
    if position.cell.is_blank():
        parent = position.cell.parent
        index = parent.index(position.cell)
        context = position.cell.context
        if context and can_insert(parent):
            if all(context.match(cell) for cell in data):
                parent.drop(index, index+1)
                parent.put(index, data)
                return Position.top(data[0]), Position.bottom(data[-1])
        replace(position.cell, ListCell(u"@", data))
        return Position.top(data[0]), Position.bottom(data[-1])
    else:
        raise Exception("not implemented")

def puttext(position, data):
    position.cell.put(position.index, data)
    return position, position + len(data)

def remove(cell):
    parent = cell.parent
    index = parent.index(cell)
    drop = parent.drop(index, index+1)
    return drop

def replace(cell, newcell):
    parent = cell.parent
    index = parent.index(cell)
    drop = parent.drop(index, index+1)
    parent.put(index, [newcell])
    return drop
