import dom
import treepython
import boxmodel
import sys
from selection import Position

class KeyEvent(object):
    def __init__(self, mode, workspace, selection, key, mods, text):
        self.mode = mode
        self.workspace = workspace
        self.selection = selection
        self.key = key
        self.mods = mods
        self.text = text

class KeyPattern(object):
    def __init__(self, key, text, mods, action):
        self.key = key
        self.text = text
        self.mods = mods
        self.action = action

    def __call__(self, event):
        triggered = False
        if self.key is not None:
            triggered |= (self.key == event.key)
        if self.text is not None:
            triggered |= (self.text == event.text)
        return triggered and self.mods.issubset(event.mods)

class Mode(object):
    def __init__(self, name, default=None, transition=None):
        self.name = name
        self.default = default
        self.transition = transition
        self.bindings = []

    def key(self, name, *mods):
        def _impl_(fn):
            self.bindings.append(KeyPattern(name, None, set(mods), fn))
            return fn
        return _impl_

    def text(self, name, *mods):
        def _impl_(fn):
            self.bindings.append(KeyPattern(None, name, set(mods), fn))
            return fn
        return _impl_

def with_transaction(fn):
    def _impl_(event):
        selection = event.selection
        transaction = event.selection.document.transaction(selection.head, selection.tail)
        try:
            fn(event)
        except Exception:
            transaction.rollback()
            selection.set(transaction.head, transaction.tail)
            raise
        else:
            transaction.commit(selection.head, selection.tail)
    return _impl_

insert = Mode('insert')
node_insert = Mode('node insert', transition=insert)

@with_transaction
def insert_default(event):
    if event.text is None:
        return
    selection = event.selection
    if selection.subj.islist():
        node = dom.Symbol(event.text)
        selection.put([node])
        event.selection.set(Position.bottom(node))
    else:
        selection.put(event.text)
insert.default = insert_default

@insert.key('left alt')
def insert_left_alt(event):
    event.mode = node_insert

@insert.key('pageup')
def insert_page_up(event):
    event.selection.visual.scroll_y -= event.selection.visual.height / 2

@insert.key('pagedown')
def insert_page_down(event):
    event.selection.visual.scroll_y += event.selection.visual.height / 2

@insert.key('space')
@with_transaction
def insert_space(event):
    selection = event.selection
    if selection.subj.isstring() or selection.subj.isbinary():
        return event.mode.default(event)
    selection.drop()
    head = selection.head
    above = head.above
    if head.subj.issymbol() and above is not None:
        newsym = dom.Symbol(head.subj.drop(head.index, len(head.subj)))
        (above+1).put([newsym])
        selection.set(Position(newsym, 0))
    if head.subj.islist():
        newsym = dom.Symbol(u"")
        selection.put([newsym])
        selection.set(Position(newsym, 0))

@insert.text(';')
def insert_jump_space(event):
    head = event.selection.head
    if head.subj.issymbol() and head.above is not None:
        above = head.above
        if head.subj.isblank():
            above.subj.drop(above.index, above.index+1)
        head = above
    above = head.above
    if above is not None:
        blank = dom.Symbol(u"")
        (above+1).put([blank])
        event.selection.set(Position(blank, 0))

#@insert.text(':')
#def insert_jump_space(event):
#    head = event.selection.head
#    if head.subj.issymbol() and head.above is not None:
#        above = head.above
#        if head.subj.isblank():
#            above.subj.drop(above.index, above.index+1)
#        head = above
#    above = head.above
#    if above is not None:
#        blank = dom.Symbol(u"")
#        above.put([blank])
#        event.selection.set(Position(blank, 0))

@insert.text(',')
def insert_capture(event):
    if selection.subj.isstring() or selection.subj.isbinary():
        return event.mode.default(event)
    sel = event.selection
    if sel.tail.subj.islist() and sel.tail.index > 0:
        tail = Position(sel.tail.subj, sel.tail.index-1)
        sel.set(sel.head, tail)
    else:
        tail = sel.tail.above
        if tail is not None:
            sel.set(sel.head, tail)

#@insert.text('.')
#def insert_fwd_capture(event):
#    sel = event.selection
#    if sel.tail.subj.islist() and sel.tail.index < len(sel.tail.subj):
#        tail = Position(sel.tail.subj, sel.tail.index+1)
#        sel.set(sel.head, tail)
#    else:
#        tail = sel.tail.above
#        if tail is not None:
#            sel.set(sel.head, tail+1)

@insert.key('backspace')
@with_transaction
def insert_backspace(event):
    sel = event.selection
    above = sel.head.above
    if sel.subj_head == sel.subj_tail and sel.subj_head > 0:
        sel.subj_head -= 1
        sel.drop()
    elif sel.head != sel.tail:
        sel.drop()
        head = sel.head
        if head.index > 0:
            sel.set(Position.bottom(head.subj[head.index-1]))
    elif len(sel.head.subj) == 0 and above is not None:
        above.subj.drop(above.index, above.index+1)
        if above.index > 0:
            sel.set(Position.bottom(above.subj[above.index-1]))
        else:
            sel.set(above)
    elif sel.head.index == 0 and above is not None and above.index > 0:
        dropsym = sel.head.subj
        putsym = above.subj[above.index-1]
        cutpoint = len(putsym)
        if dropsym.issymbol() and putsym.issymbol():
            putsym.put(cutpoint, dropsym.drop(0, len(dropsym)))
            above.subj.drop(above.index, above.index+1)
            sel.set(Position(putsym, cutpoint))

@insert.key('delete')
@with_transaction
def insert_backspace(event):
    sel = event.selection
    above = sel.head.above
    if sel.subj_head == sel.subj_tail and sel.subj_head < len(sel.subj):
        sel.subj_head += 1
        sel.drop()
    elif sel.head != sel.tail:
        sel.drop()
        head = sel.head
        if head.index < len(head.subj):
            sel.set(Position.top(head.subj[head.index]))
    elif len(sel.head.subj) == 0 and above is not None:
        above.subj.drop(above.index, above.index+1)
        if above.index < len(above.subj):
            sel.set(Position.top(above.subj[above.index]))
        else:
            sel.set(above)
    elif sel.head.index == len(sel.head.subj) and above is not None and above.index + 1 < len(above.subj):
        dropsym = sel.head.subj
        cutpoint = len(dropsym)
        putsym = above.subj[above.index+1]
        if dropsym.issymbol() and putsym.issymbol():
            putsym.put(0, dropsym.drop(0, len(dropsym)))
            above.subj.drop(above.index, above.index+1)
            sel.set(Position(putsym, cutpoint))

@insert.text("'")
@with_transaction
def insert_list(event):
    insert_new_node(event, list)

@insert.text("#")
@with_transaction
def insert_binary(event):
    insert_new_node(event, str)

@insert.text('"')
@with_transaction
def insert_string(event):
    insert_new_node(event, unicode)

def insert_new_node(event, mk_subj):
    selection = event.selection
    if selection.subj.isblank() and selection.subj.parent is not None:
        above = Position(selection.subj, 0).above
        above.subj.drop(above.index, above.index+1)
        selection.set(above)
    if selection.subj.isstring() or selection.subj.isbinary():
        return event.mode.default(event)
    if selection.subj.issymbol():
        slit(selection)
    if mk_subj is list and selection.subj.islist() and selection.subj_head != selection.subj_tail:
        sequence = selection.drop()
        new_subj = dom.Literal(u"", mk_subj(sequence))
    else:
        new_subj = dom.Literal(u"", mk_subj())
    selection.put([new_subj])
    selection.set(Position(new_subj, 0))

def slit(selection):
    head = selection.head
    if head.subj.islist():
        return
    if head.subj.parent is None:
        return
    parent = head.subj.parent
    pos = parent.index(head.subj)
    if head.index == 0:
        head.subj = parent
        head.index = pos
    elif head.index == len(head.subj):
        head.subj = parent
        head.index = pos + 1
    else:
        contents = head.subj.drop(head.index, len(head.subj))
        issymbol = head.subj.issymbol()
        head.subj = parent
        head.index = pos + 1
        if issymbol:
            head.subj.put(head.index, [dom.Symbol(contents)])
        else:
            head.subj.put(head.index, [dom.Literal(u"", contents)])
    selection.set(head, head)

@insert.key('z', 'ctrl')
def undo_document(event):
    selection = event.selection
    transaction = event.selection.document.undo()
    if transaction is not None:
        selection.set(transaction.head, transaction.tail)

@insert.key('q', 'ctrl')
def save_document(event):
    sys.exit(0)

@insert.key('s', 'ctrl')
def save_document(event):
    document = event.selection.document
    dom.save(document.name, document.body)

@insert.key('x', 'ctrl')
@with_transaction
def cut_document(event):
    event.workspace.copybuf = event.selection.drop()

@insert.key('c', 'ctrl')
def copy_document(event):
    event.workspace.copybuf = event.selection.yank()

@insert.key('v', 'ctrl')
@with_transaction
def paste_document(event):
    sel = event.selection
    copybuf = event.workspace.copybuf
    document = event.selection.document
    if copybuf is not None:
        if sel.subj.islist() and isinstance(copybuf, list):
            sel.put([node.copy() for node in copybuf])
        elif sel.subj.issymbol() and isinstance(copybuf, unicode):
            sel.put(copybuf)
        elif sel.subj.isstring() and isinstance(copybuf, unicode):
            sel.put(copybuf)
        elif sel.subj.isbinary() and isinstance(copybuf, str):
            sel.put(copybuf)

@insert.key('f5')
def evaluate_document(event):
    try:
        treepython.evaluate_document(event.selection.document)
    except treepython.SemanticErrors as ser:
        event.workspace.attach(ser.document, '<evaluation error>')
        event.selection.visual.create_layer(ser.document)

@insert.key('f12')
def debug_layout(event):
    visual = event.selection.visual
    visual.compositor.debug = not visual.compositor.debug
    visual.must_update = True

@insert.key('left')
def insert_left(event):
    head = event.selection.head
    if head.index > 0:
        if head.subj.islist():
            head = Position.bottom(head.subj[head.index-1])
        else:
            head -= 1
    else:
        head = fall_left_leaf(head.subj)
    event.selection.set(head, event.selection.tail if 'shift' in event.mods else head)

def fall_left_leaf(node):
    if node.parent is None:
        return Position.top(node)
    index = node.parent.index(node)
    if index > 0:
        return Position.bottom(node.parent[index - 1])
    else:
        return fall_left_leaf(node.parent)

@insert.key('right')
def insert_right(event):
    head = event.selection.head
    if head.index < len(head.subj):
        if head.subj.islist():
            head = Position.top(head.subj[head.index])
        else:
            head += 1
    else:
        head = fall_right_leaf(head.subj)
    event.selection.set(head, event.selection.tail if 'shift' in event.mods else None)

def fall_right_leaf(node):
    if node.parent is None:
        return Position.bottom(node)
    index = node.parent.index(node) + 1
    if index < len(node.parent):
        return Position.top(node.parent[index])
    else:
        return fall_right_leaf(node.parent)

@insert.key('up')
def insert_up(event):
    navigate(event.selection.visual, event.selection, hcarets_above, 'shift' in event.mods)

@insert.key('down')
def insert_down(event):
    navigate(event.selection.visual, event.selection, hcarets_below, 'shift' in event.mods)

def navigate(editor, sel, hcarets_fn, drag):
    caret = find_caret(editor, sel.head.subj, sel.head.index)
    if caret is None:
        return
    if sel.x_anchor is None:
        sel.x_anchor = caret.quad[0]
        if caret.index + 1 == sel.head.index:
            sel.x_anchor = caret.quad[2]
    def nearest(node):
        x0,y0,x1,y1 = node.quad
        return abs(x0 - sel.x_anchor)
    try:
        node = min(hcarets_fn(caret), key=nearest)
    except ValueError as v:
        return
    else:
        sel.set(Position(node.subj, node.index), sel.tail if drag else None)

def find_caret(editor, subj, index):
    for frame in editor.rootbox.traverse():
        if frame.subj == subj and (frame.index == index or frame.index + 1 == index):
            return frame

def hcarets_above(node):
    parent = node.parent
    success = False
    while parent is not None:
        if isinstance(parent, boxmodel.VBox):
            index = parent.index(node)
            for item in reversed(parent[:index]):
                for subnode in item.traverse():
                    if subnode.subj is not None:
                        yield subnode
                        success = True
                if success:
                    return
        node   = parent
        parent = node.parent

def hcarets_below(node):
    parent = node.parent
    success = False
    while parent is not None:
        if isinstance(parent, boxmodel.VBox):
            index = parent.index(node)
            for item in parent[index+1:]:
                for subnode in item.traverse():
                    if subnode.subj is not None:
                        yield subnode
                        success = True
                if success:
                    return
        node   = parent
        parent = node.parent

@node_insert.key('left alt')
def node_insert_editor(event):
    print 'insert editor'
    sel = event.selection
    if sel.subj.issymbol():
        subj = sel.subj.parent
    else:
        subj = sel.subj
    if subj is None:
        return

    if sel.subj_head != sel.subj_tail:
        sequence = sel.drop()
        subj = dom.Literal(u"", sequence)
        sel.put([subj])

    cache_head, cache_tail = sel.head, sel.tail

    body = dom.Symbol(subj.label)
    document = dom.Document(body)
    editor = event.selection.visual.create_sub_editor(document)
    editor.color = (0, 0, 0, 0.9)

    sel.visual = editor
    sel.set(Position.bottom(body))

    def position_hook(editor):
        editor.width = editor.parent.width
        editor.height = editor.inner_height
        editor.x = editor.parent.x
        editor.y = editor.parent.y + editor.parent.height - editor.height
    def hook(editor):
        subj.label = editor.document.body[:]
    def close_hook(editor):
        subj.label = editor.document.body[:]
        sel.visual = editor.parent
        sel.set(cache_head, cache_tail)
    editor.position_hook = position_hook
    editor.close_hook  = close_hook
    editor.update_hook = hook

@insert.key('escape')
def insert_escape(event):
    visual = event.selection.visual
    if visual.parent is not None:
        visual.close()
