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
                do_action(visual, start_completion)
            elif key == 'tab':
                if 'shift' in mod:
                    start_expansion(visual)
                    #do_action(visual, start_expansion)
                else:
                    do_action(visual, start_composition)
            elif key == 's' and 'ctrl' in mod:
                visual.document.workspace.write(visual.document)
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

def do_action(visual, action):
    if visual.action != action:
        visual.action = action
        visual.continuation = action(visual)
    try:
        visual.continuation.next()
    except StopIteration:
        visual.action = None
        visual.continuation = None

def start_completion(visual):
    head = visual.head
    assert head.cell.symbol
    result = []
    query = head.cell[:]
    for rule in head.cell.grammar.rules.values():
        if rule.label.startswith(query):
            result.append(rule)
    result.sort(key=lambda rule: rule.label)
    for rule in result:
        block = rule.blank()
        replace(head.cell, block)
        visual.setpos(Position.top(block))
        yield None
        visual.head, visual.tail = visual.document.undo()

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
    for result in parsing.parse([c.copy() for c in cell], context.rules):
        new_block = result.wrap()
        replace(cell, new_block)
        visual.setpos(Position.bottom(new_block))
        yield None
        visual.head, visual.tail = visual.document.undo()

def start_expansion(visual):
    # slightly incorrect, should find the position where expansion is allowable.
    above = visual.head.above
    forest = above.cell.drop(above.index, above.index+1)
    expansion = ListCell(u"@", forest)
    above.cell.put(above.index, [expansion])
    visual.setpos(Position(forest[0], visual.head.index))

def replace(cell, newcell):
    parent = cell.parent
    index = parent.index(cell)
    drop = parent.drop(index, index+1)
    parent.put(index, [newcell])
    return drop


def collapse(head, tail):
    if head.cell is tail.cell:
        start = min(head.index, tail.index)
        stop = max(head.index, tail.index)
        return head, head.cell.drop(start, stop)
    common, left, right = relax(head.cell.order(tail.cell))
    context = common.context
    rule = common.rule

    start = left.parent.index(left)
    stop = right.parent.index(right)+1
    while left.parent != common:
        start = left.parent.unwrap()[1]
    while right.parent != common:
        stop = right.parent.unwrap()[2]
    tempcell = ListCell(u'@', [])
    common.wrap(start, stop, tempcell)
    postorder_trim(tempcell)

    start = tempcell.index(left)
    stop = tempcell.index(right)+1
    dropped = tempcell.drop(start, stop)
    placeholder = TextCell(u"")
    tempcell.put(start, placeholder)
    if rule and not rule.validate(common):
        tempcell.unwrap()
        shred(common)
    if isinstance(rule, (Star, Plus)) and context and all(context.match(cell) for cell in tempcell):
        tempcell.unwrap()
    return Position(placeholder, 0), dropped

def relax(common, left, right):
    def flow(boundary, cell, cond, repeat):
        parent = cell.parent
        while len(parent.label) == 0 and parent != boundary and parent.is_rightmost():
            parent = parent.parent
        if parent != boundary and len(parent.label) > 0:
            if repeat:
                return flow(boundary, parent, cond, repeat)
            else:
                return parent
        else:
            return cell
    left = flow(common, left, Cell.is_leftmost, True)
    right = flow(common, right, Cell.is_rightmost, True)
    lhs = flow(None, left, Cell.is_leftmost, False)
    rhs = flow(None, right, Cell.is_rightmost, False)
    if lhs is rhs and lhs.parent is not None:
        return lhs.parent, lhs, rhs
    else:
        return common, lhs, rhs

def trim(forest, result):
    for cell in forest:
        if isinstance(cell, ListCell) and len(cell.label) == 0:
            trim(cell.dissolve(), result)
        else:
            result.append(cell)
    return result

def fault_line(target, cell, cond):
    result = []
    while cond(cell) and cell.parent != target:
        cell = cell.parent
    while cell != target:
        result.append(cell.parent.index(cell))
        cell = cell.parent
    result.reverse()
    return result


## The next three functions need to be rethought.
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

def can_carve(cell):
    rule = cell.rule
    if isinstance(rule, Star):
        return True
    if isinstance(rule, Plus) and len(cell) > 1:
        return True
    if cell.parent is None:
        return True


def join_left(position):
    lhs = Position.bottom(position.cell.previous_external)
    rhs = carve(position.cell)
    return put(lhs, rhs[:])[0]

def join_right(position):
    rhs = Position.top(position.cell.next_external)
    lhs = carve(position.cell)
    return put(rhs, lhs[:])[1]


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
        rule = position.cell.rule
        if rule:
            blank = rule.at(position.index).blank()
        else:
            blank = TextCell(u"")
        position.cell.put(position.index, [blank])
    else:
        position.cell.put(position.index, [blank])
        shred(position.cell)
    return Position.top(blank)


def put(position, data):
    if isinstance(position.cell, ListCell):
        rule = position.cell.rule
        if rule:
            blank = rule.at(position.index).blank()
        else:
            blank = TextCell(u"")
        position.cell.put(position.index, [blank])
        return put(Position.top(blank), data)
    if isinstance(data, list):
        if not position.cell.is_blank():
            split_left(position)
            split_right(position)
        assert position.cell.is_blank()
        parent = position.cell.parent
        index = parent.index(position.cell)
        context = parent.context
        rule = parent.rule
        parent.drop(index, index+1)
        if context and not all(context.match(cell) for cell in data):
            parent.put(index, [ListCell("@", [data])])
        elif not isinstance(rule, (Star, Plus)) and len(data) > 1:
            parent.put(index, [ListCell("@", [data])])
        else:
            parent.put(index, data)
        if rule and not rule.validate(parent):
            shred(parent)
        return Position.top(data[0]), Position.bottom(data[-1])
    else:
        position.cell.put(position.index, data)
        return position, position+len(data)


def carve(cell):
    "Removes the cell, no longer valid structures are shredded"
    parent = cell.parent
    index = parent.index(cell)
    rule = parent.rule
    parent.drop(index, index+1)
    if rule and not rule.validate(parent):
        shred(parent)
    return cell

def collapse_range(cell, start, stop):
    "Collapses within a cell, if the cell no longer validates, it is shredded"
    rule = cell.rule
    dropped = cell.drop(start, stop)
    placeholder = TextCell(u"")
    cell.put(start, [placeholder])
    if rule and not rule.validate(cell):
        shred(cell)
    return Position(placeholder, 0), dropped

def postorder_trim(segment):
    "Unwrap every unlabelled list cell in post-order"
    trim_out = []
    for cell in segment:
        if isinstance(cell, ListCell) and len(cell.label) == 0:
            postorder_trim(cell)
            trim_out.append(cell)
    for cell in trim_out:
        cell.unwrap()

def shred(cell):
    "Takes out all list cells belonging to a structure."
    while len(cell.label) == 0 and cell.parent:
        cell = cell.parent
    postorder_trim(new_cell)
    parent, start, stop = cell.unwrap()
    new_cell = ListCell("@", [])
    parent.wrap(start, stop, new_cell)
    return new_cell
