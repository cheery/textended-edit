from dom import TextCell, ListCell
from grammar import modeline
from position import Position
import sys
import traceback

def interpret(visual, keyboard):
    for key, mod, text in keyboard:
        try:
            print key, mod, text
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
            elif key == '\xc2':
                start_completion(visual)
            elif key == 'tab':
                start_composition(visual)
            elif key == 'left alt':
                start_expansion(visual)
            elif key == 'x' and 'ctrl' in mod:
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(position)
                position.cell.document.workspace.clipboard = clipboard
            elif key == 'v' and 'ctrl' in mod:
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(put(position, clipboard)[1])
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
            elif text == ' ':
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(position)
                if not isinstance(cliboard, list):
                    if 'shift' in mod:
                        visual.setpos(split_left(visual.head))
                    else:
                        visual.setpos(split_right(visual.head))
            elif text == '"':
                raise Exception("not implemented")
# def insert_string(visual):
#     assert visual.head.subj.isblank()
#     string = dom.Literal(u"", u"")
#     visual.head.replace([string])
#     visual.setpos(Position(string, 0))
            elif text is not None:
                position, clipboard = collapse(visual.head, visual.tail)
                visual.setpos(put(position, text)[1])
            else:
                print key, mod, text
            # cell.context
            # cell.grammar
            # cell.rule
        except Exception:
            traceback.print_exc()

def start_completion(visual):
    raise Exception("not implemented")
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


def start_composition(visual):
    raise Exception("not implemented")
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
    raise Exception("not implemented")
#     subj, left, right = head.cell.order(tail.cell)
#     g0 = fault_line(subj, left, cell.is_leftmost)
#     g1 = fault_line(subj, right, cell.is_rightmost)
#     i0 = g0.pop(0)
#     i1 = g1.pop(0)
#     while len(g0) == 0 and len(g1) == 0 and i0 == 0 and i1 == len(subj)-1 and subj.parent and len(subj.label) > 0:
#         i0 = i1 = subj.parent.index(subj)
#         subj = subj.parent
#     placeholder, dropped = crunch(visual, subj, i0, i1+1)
#     if len(dropped) == 1:
#         prefix = []
#         postfix = []
#     else:
#         leftbound = dropped.pop(0)
#         rightbound = dropped.pop(-1)
#         prefix = []
#         for i in g0:
#             sequence = dissolve(leftbound)
#             leftbound = sequence[i]
#             prefix = prefix + sequence[:i]
#             dropped = sequence[i+1:] + dropped
#         postfix = []
#         for i in g1:
#             sequence = dissolve(rightbound)
#             rightbound = sequence[i]
#             dropped = dropped + sequence[:i]
#             postfix = sequence[i+1:] + postfix
#     new_symbol = dom.Symbol(u"")
#     # to fix: use constraint-aware put here instead.
#     put(visual, placeholder, cleanup(prefix) + [new_symbol] + cleanup(postfix))
#     # to fix: if subj is no longer recognized, turn it to '@'
#     return Position(new_symbol, 0), cleanup(dropped)

def join_left(position):
    lhs = Position.bottom(position.cell.previous_external)
    rhs = carve(position)
    return put(lhs, rhs[:])[0]

def join_right(position):
    rhs = Position.top(position.cell.next_external)
    lhs = carve(position)
    return put(rhs, lhs[:])[1]

def split_left(position):
    raise Exception("not implemented")

def split_right(position):
    raise Exception("not implemented")
# def split_right(visual, position):
#     new_symbol = dom.Symbol(position.subj.drop(position.index, len(position.subj)))
#     above = position.above
#     while True:
#         if accepts_blank(visual, above.subj):
#             put(visual, insert_blank(visual, above+1), [new_symbol])
#             return Position(new_symbol, 0)
#         elif above.index == len(above.subj) - 1:
#             above = above.above
#             continue
#         if split_right_climb(visual, above.subj[above.index+1], new_symbol) is None:
#             put(visual, insert_blank(visual, above+1), [new_symbol])
#         return Position(new_symbol, 0)
# 
# def split_right_climb(visual, subj, new_symbol):
#     if subj.islist():
#         if accepts_blank(visual, subj):
#             blank = insert_blank(visual, Position(subj, 0))
#             return put(visual, blank, [new_symbol])
#         elif len(subj) > 0:
#             return split_right_climb(subj[0])

def put(position, data):
    if isinstance(position.cell, ListCell) and isinstance(data, list):
        return putforest(position, data)
    elif isinstance(position.cell, TextCell):
        return puttext(position, data)
    elif position.cell.is_external():
        blank = TextCell(u"")
        position.cell.put(0, [blank])
        return put(Position.bottom(blank), data)
    else:
        raise Exception("bad put")

def putforest(position, data):
    raise Exception("not implemented")

def puttext(position, data):
    if position.cell.is_blank():
        context = position.cell.context
        cell = TextCell(data)
        if context is not None and not context.match(cell):
            replace(position.cell, ListCell(u"@", [cell]))
        else:
            replace(position.cell, cell)
        return Position.top(cell), Position.bottom(cell)
    else:
        position.cell.put(position.index, data)
        return position, position + len(data)

def replace(cell, newcell):
    parent = cell.parent
    index = parent.index(cell)
    drop = parent.drop(index, index+1)
    parent.put(index, [newcell])
    return drop

# def space(visual):
#     assert visual.head == visual.tail
#     visual.setpos(split_right(visual, visual.head))
# 
# #    subj = visual.head.subj
# #    index = visual.head.index
# #    above = visual.head.above
# #    rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
# #    if isinstance(rule, (Star, Plus)) and isinstance(rule.rule, (Symbol, Context)) or above.subj.label == '@':
# #        if subj.isblank() and subj.parent.parent is not None:
# #            spaceWalk(visual, subj.parent)
# #            Position(subj, 0).remove()
# #        else:
# #            new_symbol = dom.Symbol(subj.drop(index, len(subj)))
# #            (above+1).put([new_symbol])
# #            visual.setpos(Position.top(new_symbol))
# #    else:
# #        spaceWalk(visual, subj)
# 
# 
# #def spaceWalk(visual, subj):
# #    above = Position(subj, 0).above
# #    rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
# #    if isinstance(rule, Sequence):
# #        if above.index+1 < len(above.subj):
# #            visual.setpos(Position.top(above.subj[above.index+1]))
# #            return
# #        else:
# #            return spaceWalk(visual, above.subj)
# #    if isinstance(rule, (Star, Plus)) and isinstance(rule.rule, (Symbol, Context)):
# #        new_symbol = dom.Symbol(u"")
# #        (above+1).put([new_symbol])
# #        visual.setpos(Position.top(new_symbol))
# #        return
# #    print visual.head.subj
# #    print visual.head.above.subj
# #    raise Exception("not implemented correctly")
# 
# 
# def put(visual, position, data):
#     if isinstance(data, list):
#         assert len(data) > 0
#         if not accepts(visual, position, data):
#             return put(visual, position, [dom.Literal(u"@", data)])
#         position.replace(data)
#         return Position.bottom(data[-1])
#     elif position.subj.islist():
#         new_symbol = dom.Symbol(unicode(data))
#         position.put([new_symbol])
#         return Position(new_symbol, len(data))
#     else:
#         position.put(data)
#         return position + len(data)
#     
# def cleanup(forest):
#     result = []
#     for tree in forest:
#         if tree.islist() and len(tree.label) == 0:
#             result.extend(cleanup(dissolve(tree)))
#         else:
#             result.append(tree)
#     return result
# 
# def dissolve(node):
#     assert node.parent == None
#     contents = node.contents
#     for node in contents:
#         node.parent = None
#     return contents
# 
# def fault_line(target, node, cond):
#     result = []
#     while cond(node) and node.parent != target:
#         node = node.parent
#     while node != target:
#         result.append(node.parent.index(node))
#         node = node.parent
#     result.reverse()
#     return result
# 
# def accepts(visual, position, data):
#     if isinstance(data, list) and len(data) == 1:
#         return accepts_item(visual, position, data[0])
#     if isinstance(data, list):
#         return accepts_list(visual, position, data)
#     rule = visual.workspace.active_schema(position.subj).recognize_in_context(position.subj)
#     if isinstance(rule, Context):
#         return any(isinstance(term, Symbol) for term in rule.valid_terms)
#     return isinstance(rule, Symbol)
# 
# def accepts_item(visual, position, node):
#     rule = visual.workspace.active_schema(position.subj).recognize_in_context(position.subj)
#     return check_item(visual, position, rule, node)
# 
# def accepts_list(visual, position, seq):
#     above = position.above
#     rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
#     if isinstance(rule, (Plus, Star)):
#         return all(check_item(visual, position, rule.rule, node) for node in seq)
# 
# def check_item(visual, position, rule, node):
#     if node.islist() and node.label == '@':
#         return True
#     result = visual.workspace.active_schema(position.subj).recognize(node)
#     if isinstance(rule, Context):
#         return True
#         #return len(rule.match(result)) > 0
#     elif isinstance(rule, Rule):
#         return rule.validate(node)
#     else:
#         return True
# 
# def insert_blank(visual, position):
#     blank = dom.Symbol(u"")
#     if accepts_blank(visual, position.subj):
#         position.put([blank])
#     else:
#         trump(position, [blank])
#     return Position(blank, 0)
# 
# def trump(position, seq):
#     base = position.above
#     base.subj.drop(base.index, base.index+1)
#     forest = dissolve(position.subj)
#     forest[position.index:position.index] = seq
#     subj = dom.Literal(u"@", cleanup(forest))
#     if len(subj) > 0:
#         base.put([subj])
# 
# def accepts_blank(visual, subj):
#     if subj.label == '@':
#         return True
#     rule = visual.workspace.active_schema(subj).recognize_in_context(subj)
#     return isinstance(rule, (Star, Plus))
# 
# def crunch(visual, subj, start, stop):
#     rule = visual.workspace.active_schema(subj).recognize_in_context(subj)
#     dropped = subj.drop(start, stop)
#     placeholder = Position(dom.Symbol(u""), 0)
#     if isinstance(rule, (Star, Plus)) or start + 1 == stop:
#         subj.put(start, [placeholder.subj])
#     else:
#         trump(Position(subj, start), [placeholder.subj])
#     return placeholder, dropped
# 
# def carve(visual, position):
#     above = position.above
#     rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
#     if isinstance(rule, Star):
#         position.replace([])
#     elif (isinstance(rule, Plus) or above.subj.label == '@') and len(above.subj) > 1:
#         position.replace([])
#     else:
#         position.replace([])
#         trump(above, [])
# 
# #    assert visual.head == visual.tail
# #    subj = visual.head.subj
# #    index = visual.head.index
# #    above = visual.head.above
# #    if index > 0:
# #        visual.head.subj.drop(visual.head.index-1, visual.head.index)
# #        visual.setpos(visual.head-1)
# #        return
# #    rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
# #    if isinstance(rule, (Star, Plus)) and isinstance(rule.rule, (Symbol, Context)) or above.subj.label == '@':
# #        if above.index > 0:
# #            prev = Position.bottom(above.subj[above.index - 1])
# #            if not prev.subj.islist():
# #                prev.put(subj[:])
# #                visual.head.remove()
# #            elif visual.head.subj.isblank():
# #                visual.head.remove()
# #            visual.setpos(prev)
# #        elif isinstance(rule, Star):
# #            visual.head.remove()
# #            visual.setpos(above)
# #        else:
# #            leftDeleteWalk(visual, subj.parent)
# #    else:
# #        leftDeleteWalk(visual, subj)
# #
# #def leftDeleteWalk(visual, subj):
# #    if subj.is_empty() and (not subj.issymbol()) and len(subj.label) > 0:
# #        new_symbol = dom.Symbol(u"")
# #        Position(subj, 0).replace([new_symbol])
# #        return visual.setpos(Position(new_symbol, 0))
# #    index = subj.parent.index(subj)
# #    if index == 0:
# #        return leftDeleteWalk(visual, subj.parent)
# #    else:
# #        return visual.setpos(Position.bottom(subj.parent[index-1]))
# 
