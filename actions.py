from selection import Position
from schema import Star, Plus, Symbol, Context
import dom
import parsing

def completion(visual):
    workspace = visual.workspace
    head = visual.head
    if visual.chain[0] == 'completion':
        _, block, result, index = visual.chain
        new_block = result[index].blank()
        Position(block, 0).replace([new_block])
        visual.setpos(
            Position.top(new_block),
            chain = ('completion',
                new_block,
                result,
                (index + 1) % len(result)))
    elif head.subj.issymbol():
        result = []
        active = workspace.active_schema(head.subj)
        name = head.subj[:]
        for rule in active.rules:
            if rule.startswith(name):
                result.append(active.rules[rule])
        block = result[0].blank()
        head.replace([block])
        visual.setpos(
            Position.top(block),
            chain = ('completion',
                block,
                result,
                1 % len(result)))
    else:
        raise Exception("not implemented")

def composition(visual):
    if visual.chain[0] == 'composition':
        _, block, result, repeat = visual.chain
        try:
            new_block = result.next().build()
            Position(block, 0).replace([new_block])
            visual.setpos(
                Position.bottom(new_block),
                chain = ('composition', new_block, result, repeat))
        except StopIteration:
            visual.setpos(
                visual.head, visual.tail,
                chain = ('composition', block, repeat(), repeat))
            return composition(visual)
    else:
        subj = visual.head.subj
        while subj.label != '@':
            subj = subj.parent
            if subj is None:
                raise Exception("not implemented")
        active = visual.workspace.active_schema(subj)
        ctx = visual.workspace.active_schema(subj).recognize_in_context(subj)
        assert isinstance(ctx, Context), ctx
        repeat = lambda: iter(parsing.parse(subj.copy(), ctx.all_valid_rules))
        result = repeat()
        new_block = result.next().build()
        Position(subj, 0).replace([new_block])
        visual.setpos(
            Position.bottom(new_block),
            chain = ('composition', new_block, result, repeat))

def pluck(visual):
    head = visual.head
    above = head.above
    block = dom.Literal(u"@", [head.subj.copy()])
    head.remove()
    above.put([block])
    visual.setpos(Position.bottom(block))

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
    if (isinstance(rule, (Star,Plus)) and isinstance(rule.rule, Symbol)) or rule == 'list' or above.subj.label == '@':
        (above+1).put([new_symbol])
        visual.setpos(Position.top(new_symbol))
    else:
        print rule
        visual.setpos(next_field(visual.workspace, above, new_symbol))

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
    visual.setpos(visual.head+1)
