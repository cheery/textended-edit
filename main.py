import treepython
import sys
import traceback
import math
import time
import font
import boxmodel
import renderers
import tempfile
import layout
import os
import defaultlayout
import importlib
from OpenGL.GL import *
from OpenGL.GL import shaders
from ctypes import c_void_p
from collections import defaultdict
import dom
from selection import Position, Selection
from ctypes import c_int, byref, c_char, POINTER, c_void_p
from sdl2 import *
from workspace import Workspace
from visual import Visual, Bridge
import sdl_backend
import keybindings

workspace = Workspace()

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

images = sdl_backend.ImageResources()

def create_editor(images):
    if len(sys.argv) > 1:
        document = workspace.get(sys.argv[1])
    else:
        document = workspace.new()
    editor = Visual(images, document, width=width, height=height)
    for path in sys.argv[2:]:
        editor.create_layer(workspace.get(path, create=False))
    return editor
editor = create_editor(images)
selection = Selection(editor, Position.bottom(editor.document.body))

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
    must_update = editor.must_update
    must_update |= configure_mapping(editor, editor.mapping, editor.document.body)
    if editor.document.ver != editor.ver or must_update:
        layout_editor(editor)
        editor.ver = editor.document.ver
        update_bridges()
        editor.must_update = False


extensions_table = {}

def configure_mapping(editor, mapping, body):
    for directive in body:
        if directive.isstring() and directive.label == 'language':
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
            return defaultlayout.build(mapping, *args)

def get_extension_layout(editor, mapping, name):
    if name in extensions_table:
        ext = extensions_table[name]
        editor.build_layout = ext.exception_catch_build
        return False
    try:
        module = importlib.import_module("extensions." + name)
    except ImportError as error:
        editor.build_layout = defaultlayout.build
        return False
    else:
        ext = Extension(module.__file__, module)
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
        if node.islist() and node.label == 'reference':
            reference = None
            target = None
            for subnode in node:
                if subnode.isbinary():
                    reference = subnode[:]
                elif subnode.islist():
                    target = subnode
            yield Bridge(layer, reference, target)

cursor = [0, 0]
def update_cursor(t):
    flatlayer.clear()
    x, y = cursor

    document = selection.document
    cursors = defaultdict(list)
    subj = selection.subj
    start = selection.start
    stop = selection.stop
    if subj not in selection.visual.mappings:
        return
    mapping = selection.visual.mappings[subj]
    if mapping.tokens is None:
        return

    color = (0, 1.0, 1.0, 0.5)
    if subj.islist():
        color = (0, 1.0, 0.0, 0.5)
    if subj.isstring():
        color = (1.0, 1.0, 0.0, 0.5)
    if subj.isbinary():
        color = (0.5, 0.0, 1.0, 0.5)

    if subj.islist():
        if start == stop:
            if start < len(subj):
                submapping = selection.visual.mappings[subj[start]]
                x0, y0, x1, y1 = submapping.tokens[0].quad
                return flatlayer.quad((x0-1, y0, x0, y1), color)
            elif len(subj) > 0:
                submapping = selection.visual.mappings[subj[-1]]
                x0, y0, x1, y1 = submapping.tokens[-1].quad
                return flatlayer.quad((x1-1, y0, x1, y1), color)
        else:
            for subnode in subj[start:stop]:
                submapping = selection.visual.mappings[subnode]
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

cursor_tail = None

def paint(t):
    #272822
    glClearColor(0x27/255.0, 0x28/255.0, 0x22/255.0, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    update_document(t)
    try:
        update_cursor(t)
    except:
        traceback.print_exc()

    scale = 1.0
    editor.compositor.render(editor.scroll_x, editor.scroll_y, width/scale, height/scale)
    for subeditor in editor.children:
        subeditor.compositor.render(-subeditor.x, -subeditor.y, width/scale, height/scale)


    flatlayer.render(editor.scroll_x, editor.scroll_y, width/scale, height/scale)

mode = keybindings.insert
keyboard = sdl_backend.KeyboardStream()
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
            if event.motion.state != 0:
                position = editor.pick(*cursor)
                if position is not None:
                    selection.visual = editor
                    selection.set(position, selection.tail)
        elif event.type == SDL_MOUSEBUTTONDOWN:
            cursor[0] = event.motion.x
            cursor[1] = event.motion.y
            sel = selection
            position = editor.pick(*cursor)
            if position is not None:
                selection.visual = editor
                selection.set(position)
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
        key_event = keybindings.KeyEvent(mode, workspace, selection, key, mod, text)
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
        if key_event.selection is not selection:
            selection = key_event.selection
    if update:
        selection.visual.update_hook(selection.visual)
    paint(time.time())
    SDL_GL_SwapWindow(window)
