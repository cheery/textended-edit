from selection import Position
from schema import Sequence, Star, Plus, Symbol, Context
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
    assert visual.head == visual.tail
    subj = visual.head.subj
    index = visual.head.index
    above = visual.head.above
    if index > 0:
        visual.head.subj.drop(visual.head.index-1, visual.head.index)
        visual.setpos(visual.head-1)
        return
    rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
    if isinstance(rule, (Star, Plus)) and isinstance(rule.rule, (Symbol, Context)) or above.subj.label == '@':
        if above.index > 0:
            prev = Position.bottom(above.subj[above.index - 1])
            prev.put(subj[:])
            visual.head.remove()
            visual.setpos(prev)
        elif isinstance(rule, Star):
            visual.head.remove()
            visual.setpos(above)
        else:
            leftDeleteWalk(visual, subj.parent)
    else:
        leftDeleteWalk(visual, subj)

def leftDeleteWalk(visual, subj):
    if subj.is_empty() and (not subj.issymbol()) and len(subj.label) > 0:
        new_symbol = dom.Symbol(u"")
        Position(subj, 0).replace([new_symbol])
        return visual.setpos(Position(new_symbol, 0))
    index = subj.parent.index(subj)
    if index == 0:
        return leftDeleteWalk(visual, subj.parent)
    else:
        return visual.setpos(Position.bottom(subj.parent[index-1]))

def delete_right(visual):
    raise Exception("not implemented")
# and not head.subj.islist():
#                    if head.index < len(head.subj):
#                        head.subj.drop(head.index, head.index+1)

def space(visual):
    assert visual.head == visual.tail
    subj = visual.head.subj
    index = visual.head.index
    above = visual.head.above
    rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
    if isinstance(rule, (Star, Plus)) and isinstance(rule.rule, (Symbol, Context)) or above.subj.label == '@':
        if subj.isblank() and subj.parent.parent is not None:
            spaceWalk(visual, subj.parent)
            Position(subj, 0).remove()
        else:
            new_symbol = dom.Symbol(subj.drop(index, len(subj)))
            (above+1).put([new_symbol])
            visual.setpos(Position.top(new_symbol))
    else:
        spaceWalk(visual, subj)

def spaceWalk(visual, subj):
    above = Position(subj, 0).above
    rule = visual.workspace.active_schema(above.subj).recognize_in_context(above.subj)
    if isinstance(rule, Sequence):
        if above.index+1 < len(above.subj):
            visual.setpos(Position.top(above.subj[above.index+1]))
            return
        else:
            return spaceWalk(visual, above.subj)
    if isinstance(rule, (Star, Plus)) and isinstance(rule.rule, (Symbol, Context)):
        new_symbol = dom.Symbol(u"")
        (above+1).put([new_symbol])
        visual.setpos(Position.top(new_symbol))
        return
    print visual.head.subj
    print visual.head.above.subj
    raise Exception("not implemented correctly")

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
