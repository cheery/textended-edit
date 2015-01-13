import gate
import sys
import traceback
import math
import time
import font
import boxmodel
import textended
import renderers
import tempfile
import layout
import os
import ast
import defaultlayout
from OpenGL.GL import *
from OpenGL.GL import shaders
from ctypes import c_void_p
from collections import defaultdict
import dom
from dom import Position, Selection
from ctypes import c_int, byref, c_char, POINTER, c_void_p
from sdl2 import *

class Editor(object):
    def __init__(self, document, selection, x=0, y=0, width=200, height=200):
        self.document = document
        self.selection = selection
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.children = []
        self.ver = 0
        self.frames = {}
        self.rootbox = None
        self.build_rootbox = None
        self.update_hook = lambda editor: None
        self.close_hook = lambda editor: None
        self.filename = None
        self.copybuf = None
        self.scroll_x = 0
        self.scroll_y = 0
        self.parent = None

    def get_rect(self, node):
        if node not in self.frames:
            return
        obj = self.frames[node].obj
        if isinstance(obj, list):
            return rect_enclosure([box.rect for box in obj if hasattr(box, 'rect')])
        elif obj is not None:
            return obj.rect

    def create_sub_editor(self, document, selection):
        subeditor = Editor(document, selection)
        subeditor.build_rootbox = self.build_rootbox
        subeditor.width = self.width
        subeditor.height = self.height
        self.children.append(subeditor)
        subeditor.parent = self
        return subeditor

module = sys.modules[__name__]

def create_editor():
    contents = []
    for path in sys.argv[1:]:
        if os.path.exists(path):
            contents.extend(dom.load(path))
    body = dom.Literal("", u"", contents)

    document = dom.Document(body)
    if len(sys.argv) == 2:
        document.filename = sys.argv[1]

    selection = Selection.bottom(body)
    editor = Editor(document, selection)
    return editor

SDL_Init(SDL_INIT_VIDEO)

editor = create_editor()
focus = editor

editor.build_rootbox = defaultlayout.build_boxmodel

SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
window = SDL_CreateWindow(b"textended-edit",
                          SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                          640, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE)
context = SDL_GL_CreateContext(window)
SDL_StartTextInput()

width = c_int()
height = c_int()
SDL_GetWindowSize(window, byref(width), byref(height))
width = width.value
height = height.value

editor.width = width
editor.height = height

editor.x += 10
editor.y += 10
editor.width  -= 20
editor.height -= 20

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

imglayer = renderers.ImageLayer()
fontlayer = renderers.FontLayer(defaultlayout.sans)
flatlayer = renderers.FlatLayer()

def burst(subj, x, y):
    subj.rect = x, y-subj.depth, subj.width, subj.height+subj.depth
    if isinstance(subj, boxmodel.HBox):
        x0 = x
        for node in subj.contents:
            if isinstance(node, boxmodel.Glue):
                x0 += node.width
            elif isinstance(node, boxmodel.LetterBox):
                x1 = x0 + node.width
                y1 = y + node.height
                y0 = y - node.depth
                s0, t0, s1, t1 = node.texcoords
                p0, p1, p2, p3 = node.padding
                c0, c1, c2, c3 = node.color
                fontlayer.quad((x0-p0, y0-p1, x1+p2, y1+p3), node.texcoords, node.color)
                x0 = x1
            elif isinstance(node, (boxmodel.HBox, boxmodel.VBox)):
                burst(node, x0, y)
                x0 += node.width
            elif isinstance(node, boxmodel.Caret):
                node.rect = x0-0.5, y-subj.depth, 1, subj.height+subj.depth
    elif isinstance(subj, boxmodel.VBox):
        y0 = y + subj.height
        for node in subj.contents:
            if isinstance(node, boxmodel.Glue):
                y0 -= node.width
            elif isinstance(node, (boxmodel.HBox, boxmodel.VBox)):
                burst(node, x, y0 - node.height)
                y0 -= node.height + node.depth
            elif isinstance(node, boxmodel.Caret):
                node.rect = x, y0-0.5, subj.width, 1

def update_characters(t):
    def layout_editor(editor, x, y):
        editor.rootbox = editor.build_rootbox(editor)
        burst(editor.rootbox, editor.x+x, editor.height - editor.y+y)
        for subeditor in editor.children:
            layout_editor(subeditor, x+editor.x, y+editor.y)
    if editor.rootbox is None or editor.document.ver != editor.ver:
        fontlayer.clear()
        layout_editor(editor, 0, 0)
        editor.ver = editor.document.ver

def delta_point_rect(point, rect):
    x0, y0 = point
    x, y, w, h = rect
    x1 = min(max(x0, x), x+w)
    y1 = min(max(y0, y), y+h)
    return (x1-x0), (y1-y0)

cursor = [0, 0]
def update_cursor(t):
    flatlayer.clear()
    x, y = cursor

    if focus.rootbox is None:
        return
    
    document = focus.document
    cursors = defaultdict(list)
    if focus.selection.subj not in focus.frames:
        return
    mapping = focus.frames[focus.selection.subj]
    if mapping.obj is None:
        return
    boxes = mapping.obj if isinstance(mapping.obj, list) else [mapping.obj]

    for box in boxes:
        for node in box.traverse():
            if not isinstance(node, boxmodel.Caret):
                continue
            if node.subj != focus.selection.subj:
                continue
            if node.index < focus.selection.start:
                continue
            if node.index > focus.selection.stop:
                continue
            cursors[node.parent].append(node.rect)

    color = (0, 1.0, 1.0, 0.5)
    if focus.selection.subj.type == 'list':
        color = (0, 1.0, 0.0, 0.5)
    if focus.selection.subj.type == 'string':
        color = (1.0, 1.0, 0.0, 0.5)
    if focus.selection.subj.type == 'binary':
        color = (0.5, 0.0, 1.0, 0.5)
    for container, cursorset in cursors.items():
        rect = rect_enclosure(cursorset)
        flatlayer.rect(rect, color)

def rect_enclosure(rects):
    x0, y0, w0, h0 = rects[0]
    x2 = x0+w0
    y2 = y0+h0
    for x1, y1, w1, h1 in rects[1:]:
        x2 = max(x2, x1+w1)
        y2 = max(y2, y1+h1)
        x0 = min(x0, x1)
        y0 = min(y0, y1)
    return x0, y0, x2-x0, y2-y0

def hierarchy_of(node):
    result = [node]
    while node.parent is not None:
        result.append(node.parent)
        node = node.parent
    result.reverse()
    return result

def simplify_selection(headpos, tailpos):
    if headpos.subj is tailpos.subj:
        return Selection(headpos.subj, headpos.index, tailpos.index)
    hh = hierarchy_of(headpos.subj)
    th = hierarchy_of(tailpos.subj)
    i = 0
    for c_a, c_b in zip(hh, th):
        if c_a is c_b:
            i += 1
        else:
            break
    assert i > 0
    subj = hh[i-1]
    head_inc = i < len(hh)
    head = subj.index(hh[i]) if head_inc else headpos.index
    tail_inc = i < len(th)
    tail = subj.index(th[i]) if tail_inc else tailpos.index
    if tail <= head:
        head += head_inc
    else:
        tail += tail_inc
    return Selection(subj, head, tail)

cursor_tail = None

def pick_nearest(editor, x, y):
    def nearest(node, maxdist):
        near, distance = None, maxdist
        if isinstance(node, boxmodel.Composite):
            dx, dy = delta_point_rect(cursor, node.rect)
            if dx**2 + dy**4 > maxdist:
                return near, distance
            for child in node:
                n, d = nearest(child, distance)
                if d < distance:
                    near = n
                    distance = d
            return near, distance
        elif is_hcaret(node):
            dx, dy = delta_point_rect(cursor, node.rect)
            return node, dx**2 + dy**4
        else:
            return None, float('inf')
    return nearest(editor.rootbox, 500**4)[0]

def is_hcaret(node):
    if isinstance(node, boxmodel.Caret):
        if not isinstance(node.subj, dom.Node):
            return
        if node.subj.type != 'list' or len(node.subj) == 0:
            return isinstance(node.parent, boxmodel.HBox)

def paint(t):
    #272822
    glClearColor(0x27/255.0, 0x28/255.0, 0x22/255.0, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    update_characters(t)
    update_cursor(t)

    if t % 5 < 0.1:
        imglayer.clear()

    w = editor.width
    h = editor.height
    x = w/4 * math.sin(t*5)
    y = h/4 * math.cos(t*3)
    imglayer.quad((w/4 + x, h/4 + y, 3* w/4 + x, 3* h/4 - y), (0, 1, 0, 1), (0.0, 0.0, 0.0, 0.02))

    imglayer.render(editor.scroll_x, editor.scroll_y, width, height)
    fontlayer.render(editor.scroll_x, editor.scroll_y, width, height)
    flatlayer.render(editor.scroll_x, editor.scroll_y, width, height)

modifiers = {
    KMOD_LSHIFT:  'left shift',
    KMOD_RSHIFT:  'right shift',
    KMOD_LCTRL:  'left ctrl',
    KMOD_RCTRL:  'right ctrl',
    KMOD_LALT:   'left alt',
    KMOD_RALT:   'right alt',
    KMOD_LGUI:  'left gui',
    KMOD_RGUI:  'right gui',
    KMOD_ALT:   'alt',
    KMOD_NUM:   'num',
    KMOD_CAPS:  'caps',
    KMOD_MODE:  'mode',
    KMOD_SHIFT: 'shift',
    KMOD_CTRL:  'ctrl',
    KMOD_GUI:   'gui',
}

class KeyboardStream(object):
    def __init__(self):
        self.name = None
        self.mods = None
        self.text = None
        self.pending = []

    def flush(self):
        if self.name is not None:
            self.pending.append((self.name, self.mods, self.text))
            self.name = None
            self.mods = None
            self.text = None

    def push_event(self, ev):
        if ev.type == SDL_TEXTINPUT:
            self.text = ev.text.text.decode('utf-8')
        if ev.type == SDL_KEYDOWN:
            sym = ev.key.keysym.sym
            mod = ev.key.keysym.mod
            self.flush()
            self.name = SDL_GetKeyName(sym).decode('utf-8').lower()
            self.mods = set(name for flag, name in modifiers.items() if mod & flag != 0)
            self.text = None

    def __iter__(self):
        self.flush()
        for key in self.pending:
            yield key
        self.pending[:] = ()

import keybindings

mode = keybindings.insert
keyboard = KeyboardStream()
event = SDL_Event()
live = True
while live:
    while SDL_PollEvent(byref(event)) != 0:
        if event.type == SDL_QUIT:
            live = False
        elif event.type == SDL_WINDOWEVENT:
            if event.window.event == SDL_WINDOWEVENT_RESIZED:
                width = event.window.data1
                height = event.window.data2

                glViewport(0, 0, width, height)
                editor.width = width
                editor.height = height
                editor.ver = 0
        elif event.type == SDL_MOUSEMOTION:
            cursor[0] = event.motion.x
            cursor[1] = height - event.motion.y
            if event.motion.state == 0:
                cursor_tail = None
            if cursor_tail is not None:
                node = pick_nearest(focus, event.motion.x, event.motion.y)
                if node is not None:
                    focus.headpos = Position(node.subj, node.index)
                    focus.selection = simplify_selection(focus.headpos, focus.tailpos)
        elif event.type == SDL_MOUSEBUTTONDOWN:
            sel = focus.selection
            node = pick_nearest(focus, event.button.x, event.button.y)
            if node is not None:
                sel.subj = node.subj
                sel.head = sel.tail = node.index
                sel.x_anchor = None
                cursor_tail = Position(node.subj, node.index)
                focus.headpos = focus.tailpos = cursor_tail
                focus.selection = simplify_selection(focus.headpos, focus.tailpos)
        elif event.type == SDL_MOUSEBUTTONUP:
            pass
        else:
            keyboard.push_event(event)

    update = False
    for key, mod, text in keyboard:
        update = True
        key_event = keybindings.KeyEvent(mode, focus, key, mod, text)
        valid = [binding for binding in mode.bindings if binding(key_event)]
        try:
            if len(valid) > 1:
                print "more than one keybinding"
            elif len(valid) == 1:
                valid[0].action(key_event)
            elif mode.default is not None:
                mode.default(key_event)
        except Exception as exc:
            traceback.print_exc()
        if key_event.mode is not mode:
            mode = key_event.mode
        elif mode.transition is not None:
            mode = mode.transition
        if key_event.editor is not focus:
            focus = key_event.editor
    if update:
        focus.update_hook(focus)
    paint(time.time())
    SDL_GL_SwapWindow(window)
