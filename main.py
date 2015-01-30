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
from panels import Panels
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
        'background': (0x27/255.0, 0x28/255.0, 0x22/255.0, 1), #272822
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
    editor = Visual(default_env, images, document, width=width, height=height)
    for path in sys.argv[2:]:
        editor.create_layer(workspace.get(path, create=False))
    return editor
editor = create_editor(images)
selection = Selection(editor, Position.bottom(editor.document.body))

panels = Panels(default_env, images, 0, 0, width, height)
panels.panes.append(editor)
panels.panes.append(create_editor(images))

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
flatlayer = renderers.FlatLayer()

def paint(t):
    glClearColor(*default_env['background'])
    glClear(GL_COLOR_BUFFER_BIT)

    try:
        panels.update()
        update_cursor(t)
    except:
        traceback.print_exc()

    scale = 1.0
    panels.render(width, height)

    visual = selection.visual
    flatlayer.render(-visual.x + visual.scroll_x, -visual.y + visual.scroll_y, width/scale, height/scale)

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

    for container, quads in cursors.items():
        x0, y0, x1, y1 = quads[0]
        for x2, y2, x3, y3 in quads[1:]:
            x0 = min(x0, x2)
            y0 = min(y0, y2)
            x1 = max(x1, x3)
            y1 = max(y1, y3)
        flatlayer.quad((x0,y0,x1,y1), color)

def pick(visual, x, y, drag=False):
    if visual.children:
        for child in visual.children:
            pick(child, x, y, drag)
    else:
        position = visual.pick(x - visual.x + visual.scroll_x, y - visual.y + visual.scroll_y)
        if position is not None:
            selection.visual = visual
            selection.set(position, selection.tail if drag else None)

def pick_panels(visual, x, y, drag=False):
    for pane in panels.panes:
        if 0 <= x - pane.x < pane.width and 0 <= y - pane.y < pane.height:
            pick(pane, x, y, drag)

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
                panels.width = width
                panels.height = height
        elif event.type == SDL_MOUSEMOTION:
            cursor[0] = event.motion.x
            cursor[1] = event.motion.y
            if event.motion.state != 0:
                pick_panels(editor, cursor[0], cursor[1], True)
        elif event.type == SDL_MOUSEBUTTONDOWN:
            cursor[0] = event.motion.x
            cursor[1] = event.motion.y
            pick_panels(editor, cursor[0], cursor[1], False)
        elif event.type == SDL_MOUSEBUTTONUP:
            pass
        elif event.type == SDL_MOUSEWHEEL:
            selection.visual.scroll_x -= event.wheel.x * 10.0
            selection.visual.scroll_y -= event.wheel.y * 10.0
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
