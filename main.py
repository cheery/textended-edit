import treepython
import extensions
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
import imp
from mapping import Mapping
from compositor import Compositor
from OpenGL.GL import *
from OpenGL.GL import shaders
from ctypes import c_void_p
from collections import defaultdict
import dom
from dom import Position, Selection
from ctypes import c_int, byref, c_char, POINTER, c_void_p
from sdl2 import *
from workspace import Workspace

workspace = Workspace()

debug_layout = False

default_env = {
        'font': font.load('OpenSans.fnt'),
        'fontsize': 10,
        'white': (1.0, 1.0, 1.0, 1.0),
        'blue': (0.5, 0.5, 1.0, 1.0),
        'green': (1.0, 1.0, 0.0, 1.0),
        'yellow': (1.0, 1.0, 0.0, 1.0),
        'pink': (1.0, 0.0, 1.0, 1.0),
        'gray': (0.5, 0.5, 0.5, 1.0),
}

class Editor(object):
    def __init__(self, images, document, selection, x=0, y=0, width=200, height=200):
        self.images = images
        self.compositor = Compositor(images, debug_layout)
        self.document = document
        self.selection = selection
        self.layers = []
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.children = []
        self.ver = 0
        self.mappings = {}
        self.mapping = Mapping(self.mappings, self.document.body, None)
        self.build_layout = defaultlayout.build
        self.rootbox = None
        self.bridges = []
        self.position_hook = lambda editor: None
        self.update_hook = lambda editor: None
        self.close_hook = lambda editor: None
        self.copybuf = None
        self.scroll_x = 0
        self.scroll_y = 0
        self.parent = None
        self.background = None
        self.color = None

    def close(self):
        self.compositor.close()
        self.close_hook(self)
        if self.parent is not None:
            self.parent.children.remove(self)

    def get_rect(self, node):
        if node not in self.mappings:
            return
        obj = self.mappings[node].obj
        if isinstance(obj, list):
            return rect_enclosure([box.rect for box in obj if hasattr(box, 'rect')])
        elif obj is not None:
            return obj.rect

    def create_sub_editor(self, document, selection):
        subeditor = Editor(self.images, document, selection)
        subeditor.width = self.width
        subeditor.height = self.height
        self.children.append(subeditor)
        subeditor.parent = self
        return subeditor

    def create_layer(self, document):
        print 'layer created'
        layer = EditorLayer(document)
        self.layers.append(layer)
        self.ver = 0
        return layer

class EditorLayer(object):
    def __init__(self, document):
        self.document = document
        self.ver = 0
        self.build_rootbox = None

class Bridge(object):
    def __init__(self, layer, reference, body):
        self.layer = layer
        self.reference = reference
        self.body = body
        self.mappings = {}
        self.mapping = Mapping(self.mappings, body, None)
        self.build_layout = defaultlayout.build
        self.rootbox = None

module = sys.modules[__name__]

SDL_Init(SDL_INIT_VIDEO)
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

images = renderers.ImageResources()

def create_editor(images):
    if len(sys.argv) > 1:
        document = workspace.get(sys.argv[1])
    else:
        document = workspace.new()
    selection = Selection.bottom(document.body)
    editor = Editor(images, document, selection)
    for path in sys.argv[2:]:
        editor.create_layer(workspace.get(path, create=False))
    return editor
editor = create_editor(images)
focus = editor
editor.width = width
editor.height = height

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
flatlayer = renderers.FlatLayer()

def update_document(t):
    def layout_editor(editor):
        editor.mappings.clear()
        editor.compositor.clear()
        editor.rootbox = boxmodel.vpack(editor.mapping.update(editor.build_layout, default_env))
        editor.inner_width = editor.rootbox.width + 20
        editor.inner_height = editor.rootbox.vsize + 20
        editor.position_hook(editor)
        editor.compositor.clear()
        editor.compositor.decor((0, 0, editor.width, editor.height), editor.background, editor.color)
        editor.compositor.compose(editor.rootbox, 10, 10 + editor.rootbox.height)
        for subeditor in editor.children:
            layout_editor(subeditor)
    must_update = configure_mapping(editor, editor.mapping, editor.document.body)
    if editor.document.ver != editor.ver or must_update:
        layout_editor(editor)
        editor.ver = editor.document.ver
        update_bridges()


extensions_table = {}

def configure_mapping(editor, mapping, body):
    for directive in body:
        if directive.type == 'string' and directive.label == 'language':
            name = directive[:]
            return get_extension_layout(editor, mapping, name)
    return False

class Extension(object):
    def __init__(self, path, module):
        self.path = path
        self.module = module

    def exception_catch_build(self, mapping, *args):
        try:
            return iter(self.module.layout(mapping, *args))
        except Exception as error:
            traceback.print_exc()
            mapping.func = defaultlayout.build
            return defaultlayout.build(mapping, *args)

def get_extension_layout(editor, mapping, name):
    if name in extensions_table:
        ext = extensions_table[name]
        if ext.last_check + 1.0 < time.time():
            ext.last_check = time.time()
            mtime = os.path.getmtime(ext.path)
            if ext.mtime >= mtime:
                return False 
        else:
            return False
    path = "extensions/" + name + "/__init__.t+"
    py_path = "extensions/" + name + "/__init__.py"
    modname = "extensions." + name
    if os.path.exists(path):
        module = treepython.import_file_to_module("extensions." + name, path)
    elif os.path.exists(py_path):
        module = imp.load_source(modname, py_path)
        path = py_path
    else:
        editor.build_layout = defaultlayout.build
        return False
    ext = Extension(path, module)
    ext.last_check = time.time()
    ext.mtime = os.path.getmtime(ext.path)
    extensions_table[name] = ext
    print "loaded language module", name
    editor.build_layout = ext.exception_catch_build
    return True

def update_bridges():
    editor.bridges = []
    for layer in editor.layers:
        editor.bridges.extend(collect_bridges(layer))
    sectors = []
    for bridge in editor.bridges:
        referenced = editor.document.nodes.get(bridge.reference)
        if referenced not in editor.mappings:
            continue
        bridge.rootbox = boxmodel.vpack(bridge.mapping.update(bridge.build_layout, default_env))
        x0, y0, x1, y1 = editor.mappings[referenced].tokens[0].quad
        editor.compositor.decor((x0,y0,x1,y1), boxmodel.Patch9("assets/border-1px.png"), (1.0, 0.0, 0.0, 0.25))
        bridge.y = y0
        sectors.append(bridge)
    sectors.sort(key=lambda b: b.y)
    max_y = 0
    for bridge in sectors:
        y = max(bridge.y, max_y)
        editor.compositor.compose(bridge.rootbox, editor.rootbox.width + 50, y)
        max_y = y + bridge.rootbox.vsize

def update_characters(t):
    def layout_editor(editor):
        editor.rootbox = editor.build_rootbox(editor.mappings, editor.document.body)
        editor.inner_width = editor.rootbox.width + 20
        editor.inner_height = editor.rootbox.vsize + 20
        editor.position_hook(editor)
        editor.compositor.clear()
        editor.compositor.decor((0, 0, editor.width, editor.height), editor.background, editor.color)
        editor.compositor.compose(editor.rootbox, 10, 10 + editor.rootbox.height)
        for subeditor in editor.children:
            layout_editor(subeditor)
    if editor.rootbox is None or editor.document.ver != editor.ver:
        layout_editor(editor)
        editor.ver = editor.document.ver
        editor.bridges = []
        for layer in editor.layers:
            editor.bridges.extend(collect_bridges(layer))
        sectors = []
        for bridge in editor.bridges:
            referenced = editor.document.nodes.get(bridge.reference)
            if referenced not in editor.mappings:
                continue
            bridge.rootbox = bridge.layer.build_rootbox(bridge.mappings, bridge.body)
            x0, y0, x1, y1 = editor.mappings[referenced].tokens[0].quad
            editor.compositor.decor((x0,y0,x1,y1), boxmodel.Patch9("assets/border-1px.png"), (1.0, 0.0, 0.0, 0.25))
            bridge.y = y0
            sectors.append(bridge)
        sectors.sort(key=lambda b: b.y)
        max_y = 0
        for bridge in sectors:
            y = max(bridge.y, max_y)
            editor.compositor.compose(bridge.rootbox, editor.rootbox.width + 50, y)
            max_y = y + bridge.rootbox.vsize

def collect_bridges(layer):
    for node in layer.document.body:
        if node.type == 'list' and node.label == 'reference':
            reference = None
            target = None
            for subnode in node:
                if subnode.type == 'binary':
                    reference = subnode[:]
                elif subnode.type == 'list':
                    target = subnode
            yield Bridge(layer, reference, target)

def delta_point_quad(point, quad):
    x, y = point
    x0, y0, x1, y1 = quad
    return min(max(x0, x), x1) - x, min(max(y0, y), y1) - y

cursor = [0, 0]
def update_cursor(t):
    flatlayer.clear()
    x, y = cursor

    document = focus.document
    cursors = defaultdict(list)
    subj = focus.selection.subj
    start = focus.selection.start
    stop = focus.selection.stop
    if subj not in focus.mappings:
        return
    mapping = focus.mappings[subj]
    if mapping.tokens is None:
        return

    color = (0, 1.0, 1.0, 0.5)
    if subj.type == 'list':
        color = (0, 1.0, 0.0, 0.5)
    if subj.type == 'string':
        color = (1.0, 1.0, 0.0, 0.5)
    if subj.type == 'binary':
        color = (0.5, 0.0, 1.0, 0.5)

    if subj.type == 'list':
        if start == stop:
            if start < len(subj):
                submapping = focus.mappings[subj[start]]
                x0, y0, x1, y1 = submapping.tokens[0].quad
                return flatlayer.quad((x0-1, y0, x0, y1), color)
            elif len(subj) > 0:
                submapping = focus.mappings[subj[-1]]
                x0, y0, x1, y1 = submapping.tokens[-1].quad
                return flatlayer.quad((x1-1, y0, x1, y1), color)
        else:
            for subnode in subj[start:stop]:
                submapping = focus.mappings[subnode]
                for token in submapping.tokens:
                    cursors[token.parent].append(token.quad)

    for box in mapping.tokens:
        for node in box.traverse():
            if node.subj != subj:
                continue
            if start == stop:
                if node.index == start:
                    x0, y0, x1, y1 = node.quad
                    caret = (x0-1, y0, x0, y1)
                    return flatlayer.quad(caret, color)
                if node.index + 1 == start:
                    x0, y0, x1, y1 = node.quad
                    caret = (x1-1, y0, x1, y1)
                    return flatlayer.quad(caret, color)
            elif start <= node.index < stop:
                cursors[node.parent].append(node.quad)

    for container, cursorset in cursors.items():
        quad = quad_enclosure(cursorset)
        flatlayer.quad(quad, color)

def quad_enclosure(quads):
    x0, y0, x1, y1 = quads[0]
    for x2, y2, x3, y3 in quads[1:]:
        x0 = min(x0, x2)
        y0 = min(y0, y2)
        x1 = max(x1, x3)
        y1 = max(y1, y3)
    return x0, y0, x1, y1

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
    cursor = x, y
    def nearest(node, maxdist):
        near, distance = None, maxdist
        if isinstance(node, boxmodel.Composite):
            dx, dy = delta_point_quad(cursor, node.quad)
            if dx**2 + dy**4 > maxdist:
                return near, distance
            for child in node:
                n, d = nearest(child, distance)
                if d < distance:
                    near = n
                    distance = d
            return near, distance
        elif is_hcaret(node):
            dx, dy = delta_point_quad(cursor, node.quad)
            offset = (x - (node.quad[0] + node.quad[2])*0.5) > 0
            return Position(node.subj, node.index + offset), dx**2 + dy**4
        else:
            return None, float('inf')
    return nearest(editor.rootbox, 500**4)[0]

def is_hcaret(node):
    return isinstance(node.subj, dom.Node)

def paint(t):
    #272822
    glClearColor(0x27/255.0, 0x28/255.0, 0x22/255.0, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    update_document(t)
    update_cursor(t)

    scale = 1.0
    editor.compositor.render(editor.scroll_x, editor.scroll_y, width/scale, height/scale)
    for subeditor in editor.children:
        subeditor.compositor.render(-subeditor.x, -subeditor.y, width/scale, height/scale)


    flatlayer.render(editor.scroll_x, editor.scroll_y, width/scale, height/scale)

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
            cursor[1] = event.motion.y
            if event.motion.state == 0:
                cursor_tail = None
            if cursor_tail is not None:
                position = pick_nearest(focus, cursor[0], cursor[1])
                if position is not None:
                    focus.headpos = position
                    focus.selection = simplify_selection(focus.headpos, focus.tailpos)
        elif event.type == SDL_MOUSEBUTTONDOWN:
            cursor[0] = event.motion.x
            cursor[1] = event.motion.y
            sel = focus.selection
            position = pick_nearest(focus, cursor[0], cursor[1])
            if position is not None:
                sel.subj = position.subj
                sel.head = sel.tail = position.index
                sel.x_anchor = None
                cursor_tail = position
                focus.headpos = focus.tailpos = cursor_tail
                focus.selection = simplify_selection(focus.headpos, focus.tailpos)
        elif event.type == SDL_MOUSEBUTTONUP:
            pass
        elif event.type == SDL_MOUSEWHEEL:
            editor.scroll_x -= event.wheel.x * 10.0
            editor.scroll_y -= event.wheel.y * 10.0
        else:
            keyboard.push_event(event)

    update = False
    for key, mod, text in keyboard:
        update = True
        key_event = keybindings.KeyEvent(mode, workspace, focus, key, mod, text)
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
