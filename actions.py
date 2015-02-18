from selection import Position
import dom
from schema import Star, Plus, Symbol

def completion(visual):
    workspace = visual.workspace
    head = visual.head
    if head.subj.issymbol():
        result = []
        active = workspace.active_schema(head.subj)
        name = head.subj[:]
        for rule in active.rules:
            if rule.startswith(name):
                result.append(rule)
        block = active.rules[result.pop(0)].blank()
        head.replace([block])
        visual.tail = visual.head = Position.top(block)
    else:
        raise Exception("not implemented")

#                elif 'left alt' in mod and text != None and head.subj.isblank():
#                    result = []
#                    active = workspace.active_schema(head.subj)
#                    for rule in active.rules:
#                        if rule.startswith(text):
#                            result.append(rule)
#                    block = active.rules[result.pop(0)].blank()
#                    subj = head.subj
#                    parent = subj.parent
#                    index = parent.index(subj)
#                    parent.drop(index, index+1)
#                    parent.put(index, [block])
#                    tail = head = Position.top(block)

def delete_left(visual):
    raise Exception("not implemented")
#    and not head.subj.islist():
#    if head.index > 0:
#        head.subj.drop(head.index-1, head.index)
#        tail = head = Position(head.subj, head.index-1)

def delete_right(visual):
    raise Exception("not implemented")
# and not head.subj.islist():
#                    if head.index < len(head.subj):
#                        head.subj.drop(head.index, head.index+1)

def space(visual):
    assert visual.head.subj.issymbol()
    subj = visual.head.subj
    index = visual.head.index
    above = visual.head.above
    if subj.isblank():
        visual.head.remove()
        visual.tail = visual.head = next_field(visual.workspace, above, subj)
        return
    new_symbol = dom.Symbol(subj.drop(index, len(subj)))
    rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
    if (isinstance(rule, (Star,Plus)) and isinstance(rule.rule, Symbol)) or rule == 'list':
        (above+1).put([new_symbol])
        visual.tail = visual.head = Position.top(new_symbol)
    elif isinstance(rule, (Star,Plus)):
        visual.head.remove()
        above.put([dom.Literal(u"@", [subj, new_symbol])])
        visual.tail = visual.head = Position.top(new_symbol)
    else:
        visual.tail = visual.head = next_field(visual.workspace, above, new_symbol)

def next_field(workspace, position, new_symbol):
    above = position.above
    if above is None:
        (position+1).put([new_symbol])
        return Position.top(new_symbol)
    rule = workspace.active_schema(above.subj).recognize_in_context(above.subj)
    if isinstance(rule, (Star, Plus)):
        (above+1).put([new_symbol])
        return Position.top(new_symbol)
    else:
        raise Exception(repr(rule))
        return next_field(workspace, above)

def insert_string(visual):
    raise Exception("not implemented")
    head.subj.isblank()
    string = dom.Literal(u"", u"")
    subj = head.subj
    parent = subj.parent
    index = parent.index(subj)
    parent.drop(index, index+1)
    parent.put(index, [string])
    tail = head = Position(string, 0)

def insert_text(visual, text):
    if visual.head.subj.islist():
        # should advance until this operation doesn't violate a schema.
        blank = dom.Symbol(u"")
        visual.head.put([blank])
        visual.head = Position(blank, 0)
    visual.head.put(text)
    visual.tail = visual.head = visual.head+1
