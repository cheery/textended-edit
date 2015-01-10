import dom

class KeyEvent(object):
    def __init__(self, mode, editor, key, mods, text):
        self.mode = mode
        self.editor = editor
        self.key = key
        self.mods = mods
        self.text = text

class KeyPattern(object):
    def __init__(self, key, mods, action):
        self.key = key
        self.mods = mods
        self.action = action

    def __call__(self, event):
        return (self.key == event.key or self.key == event.text) and self.mods.issubset(event.mods)

class Mode(object):
    def __init__(self, name, default=None, transition=None):
        self.name = name
        self.default = default
        self.transition = transition
        self.bindings = []

    def key(self, name, *mods):
        def _impl_(fn):
            self.bindings.append(KeyPattern(name, set(mods), fn))
            return fn
        return _impl_

insert = Mode('insert')
node_insert = Mode('node insert', transition=insert)

def insert_default(event):
    if event.text is None:
        return
    selection = event.editor.selection
    if selection.subj.type in ('string', 'symbol', 'binary'):
        selection.put(event.text)
    else:
        node = dom.Symbol(event.text)
        selection.put([node])
        event.editor.selection = dom.Selection.bottom(node)
insert.default = insert_default

@insert.key('left alt')
def insert_left_alt(event):
    event.mode = node_insert

@insert.key('pageup')
def insert_page_up(event):
    event.editor.scroll_y += event.editor.height / 2

@insert.key('pagedown')
def insert_page_down(event):
    event.editor.scroll_y -= event.editor.height / 2

@insert.key('space')
def insert_space(event):
    selection = event.editor.selection
    if selection.subj.type in ('string', 'binary'):
        return event.mode.default(event)
    if selection.subj.type == 'symbol':
        slit(selection)

@insert.key('backspace')
def insert_backspace(event):
    sel = event.editor.selection
    if sel.head == sel.tail and sel.head > 0:
        sel.head -= 1
    sel.drop()

@insert.key('delete')
def insert_delete(event):
    sel = event.editor.selection
    if sel.head == sel.tail and sel.head < len(sel.subj):
        sel.head += 1
    sel.drop()

@insert.key('escape')
def insert_escape(event):
    print "close hook"

@insert.key("'")
def insert_list(event):
    insert_new_node(event, list)

@insert.key("#")
def insert_binary(event):
    insert_new_node(event, str)

@insert.key('"')
def insert_string(event):
    insert_new_node(event, unicode)

def insert_new_node(event, mk_subj):
    selection = event.editor.selection
    if selection.subj.type in ('string', 'binary'):
        return event.mode.default(event)
    if selection.subj.type == 'symbol':
        slit(selection)
    new_subj = dom.Literal("", u"", mk_subj())
    selection.put([new_subj])
    selection.subj = new_subj
    selection.head = selection.tail = 0
    selection.x_anchor = None

def slit(sel):
    if sel.subj.type == 'list':
        return
    if sel.subj.parent is None:
        return
    parent = sel.subj.parent
    pos = parent.index(sel.subj)
    if sel.head != sel.tail:
        sel.drop()
    if sel.head == 0:
        sel.subj = parent
        sel.head = sel.tail = pos
    if sel.head == len(sel.subj):
        sel.subj = parent
        sel.head = sel.tail = pos + 1
    else:
        contents = sel.subj.drop(sel.head, len(sel.subj))
        type = sel.subj.type
        sel.subj = parent
        sel.head = sel.tail = pos + 1
        if type == 'symbol':
            sel.subj.put(sel.head, [dom.Symbol(contents)])
        else:
            sel.subj.put(sel.head, [dom.Literal("", u"", contents)])

@insert.key('(')
def insert_fall_left(event):
    fall_before(event.editor.selection)

def fall_before(sel):
    type = sel.subj.type
    parent = sel.subj.parent
    if parent is None:
        return
    pos = parent.index(sel.subj)
    sel.subj = parent
    sel.head = sel.tail = pos
    if type != 'list':
        fall_before(sel)

@insert.key(')')
def insert_fall_right(event):
    fall_after(event.editor.selection)

def fall_after(sel):
    type = sel.subj.type
    parent = sel.subj.parent
    if parent is None:
        return
    pos = parent.index(sel.subj) + 1
    sel.subj = parent
    sel.head = sel.tail = pos
    if type != 'list':
        fall_after(sel)

@insert.key('left')
def insert_left(event):
    sel = event.editor.selection
    if sel.head > 0:
        if sel.subj.type == 'list':
            sel = dom.Selection.bottom(sel.subj[sel.head-1])
        else:
            sel.head -= 1
            sel.tail = sel.head
            sel.x_anchor = None
    else:
        sel = fall_left_leaf(sel.subj)
    event.editor.selection = sel

def fall_left_leaf(node):
    if node.parent is None:
        return dom.Selection.top(node)
    index = node.parent.index(node)
    if index > 0:
        return dom.Selection.bottom(node.parent[index - 1])
    else:
        return fall_left_leaf(node.parent)

@insert.key('right')
def insert_right(event):
    sel = event.editor.selection
    if sel.head < len(sel.subj):
        if sel.subj.type == 'list':
            sel = dom.Selection.top(sel.subj[sel.head])
        else:
            sel.head += 1
            sel.tail = sel.head
            sel.x_anchor = None
    else:
        sel = fall_right_leaf(sel.subj)
    event.editor.selection = sel

def fall_right_leaf(node):
    if node.parent is None:
        return dom.Selection.bottom(node)
    index = node.parent.index(node) + 1
    if index < len(node.parent):
        return dom.Selection.top(node.parent[index])
    else:
        return fall_right_leaf(node.parent)

@insert.key('s', 'ctrl')
def save_document(event):
    document = event.editor.document
    dom.save(document.filename, document.body)

@insert.key('x', 'ctrl')
def cut_document(event):
    selection = event.editor.selection
    document = event.editor.document
    document.copybuf = selection.drop()

@insert.key('c', 'ctrl')
def copy_document(event):
    selection = event.editor.selection
    document = event.editor.document
    document.copybuf = selection.yank()

@insert.key('v', 'ctrl')
def paste_document(event):
    sel = event.editor.selection
    document = event.editor.document
    if document.copybuf is not None:
        if sel.subj.type == 'list' and isinstance(document.copybuf, list):
            sel.put(document.copybuf)
        elif sel.subj.type == 'symbol' and isinstance(document.copybuf, unicode):
            sel.put(document.copybuf)
        elif sel.subj.type == 'string' and isinstance(document.copybuf, unicode):
            sel.put(document.copybuf)
        elif sel.subj.type == 'binary' and isinstance(document.copybuf, str):
            sel.put(document.copybuf)
