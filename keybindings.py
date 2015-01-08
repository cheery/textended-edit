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
        return self.key == event.key and self.mods.issubset(event.mods)

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
        print event.key
        return
    selection = event.editor.selection
    if selection.subj.type in ('string', 'symbol', 'binary'):
        selection.put(event.text)
    else:
        node = dom.Symbol(event.text)
        selection.put([node])
        event.editor.selection = dom.Selection.bottom(node)
insert.default = insert_text

@insert.key('left alt')
def insert_left_alt(event):
    event.mode = node_insert

@insert.key('pageup')
def insert_page_up(event):
    event.editor.scroll_y += event.editor.height / 2

@insert.key('pagedown')
def insert_page_down(event):
    event.editor.scroll_y -= event.editor.height / 2
