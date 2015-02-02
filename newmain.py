from boxmodel import *
from compositor import Compositor
from ctypes import c_int, byref, c_char, POINTER, c_void_p
from newdom import Document, Symbol
from math import sin, cos
from OpenGL.GL import *
from sdl2 import *
import font
import sdl_backend
import time
import traceback
import sys

class Object(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])

class Position(object):
    def __init__(self, pos, index):
        self.pos = pos
        self.index = index

    def __cmp__(self, other):
        return cmp((self.pos, self.index), (other.pos, other.index))

def init():
    global window, context, images, middle, front, document, env, head, tail
    SDL_Init(SDL_INIT_VIDEO)
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    window = SDL_CreateWindow(b"textended-edit",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        640, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE)
    context = SDL_GL_CreateContext(window)
    images = sdl_backend.ImageResources()
    SDL_StartTextInput()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    middle = Compositor(images)
    front = Compositor(images)

    document = Document([
        Symbol("Hello"),
        Symbol("World")
    ])
    env = Object(
        background=(0x27/255.0, 0x28/255.0, 0x22/255.0, 1), #272822
        white=(1.0, 1.0, 1.0, 1.0),
        blue=(0.5, 0.5, 1.0, 1.0),
        green=(1.0, 1.0, 0.0, 1.0),
        yellow=(1.0, 1.0, 0.0, 1.0),
        pink=(1.0, 0.0, 1.0, 1.0),
        gray=(0.5, 0.5, 0.5, 1.0),
        fontsize=12,
        font=font.load("OpenSans.fnt"))
    head = Position(len(document)-1, len(document[-1]))
    tail = Position(len(document)-1, len(document[-1]))

def main(respond):
    global head
    keyboard = sdl_backend.KeyboardStream()
    event = SDL_Event()
    running = True
    while running:
        respond()
        while SDL_PollEvent(byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
            elif event.type == SDL_MOUSEMOTION:
                if event.motion.state != 0:
                    pick(event.motion.x, event.motion.y, True)
            elif event.type == SDL_MOUSEBUTTONDOWN:
                pick(event.motion.x, event.motion.y)
            #elif event.type == SDL_MOUSEWHEEL:
            #    selection.visual.scroll_x -= event.wheel.x * 10.0
            #    selection.visual.scroll_y -= event.wheel.y * 10.0
            else:
                keyboard.push_event(event)
        for key, mod, text in keyboard:
            try:
                print key, mod, text
                if key == 'escape':
                    sys.exit(0)
                if key == 'f12':
                    middle.debug = not middle.debug
                    front.debug = not front.debug
                if key == 'space':
                    symbol = document[head.pos]
                    document.put(head.pos+1, [Symbol(symbol.drop(head.index, len(symbol)))])
                    head = Position(head.pos+1, 0)
                elif text is not None:
                    symbol = document[head.pos]
                    symbol.put(head.index, text)
                    head = Position(head.pos, head.index + len(text))
            except Exception:
                traceback.print_exc()
        paint(time.time())
        SDL_GL_SwapWindow(window)

def pick(x, y, drag=False):
    global head, tail
    nearest = None
    distance = 500**4
    for subbox in rootbox.traverse():
        if subbox.subj is not None:
            x0, y0, x1, y1 = subbox.quad
            dx = clamp(x, x0, x1) - x
            dy = clamp(y, y0, y1) - y
            d = dx**4 + dy**2
            if d < distance:
                distance = d
                nearest = subbox
    if nearest is not None:
        head = Position(document.contents.index(nearest.subj), nearest.index)
        if not drag:
            tail = head

def paint(t):
    global rootbox
    width, height = get_window_size()
    glViewport(0, 0, width, height)
    glClearColor(*env.background)
    glClear(GL_COLOR_BUFFER_BIT)
    middle.clear()
    front.clear()

    rootbox = layout(document)
    middle.compose(rootbox, 10, 50)

    start = min(head, tail)
    stop = max(head, tail)
    for subbox in rootbox.traverse():
        if subbox.subj is document[head.pos] and subbox.index == head.index:
            x0, y0, x1, y1 = subbox.quad
            front.decor((x0, y0, x0+2, y1), None, (1, 0, 0, 1))

        if subbox.subj is not None:
            pos = document.contents.index(subbox.subj)
            if start.pos == stop.pos == pos:
                if start.index < subbox.index < stop.index:
                    front.decor(subbox.quad, None, (1, 0, 0, 0.5))
            elif start.pos <= pos <= stop.pos:
                front.decor(subbox.quad, None, (1, 0, 0, 0.5))

    middle.render(0, 0, width, height)
    front.render(0, 0, width, height)

def layout(document):
    tokens = []
    for node in document:
        if len(tokens) > 0:
            tokens.extend(env.font(' ', env.fontsize))
        if isinstance(node, Symbol) and len(node) == 0:
            box = hpack(env.font("___", env.fontsize, color=env.blue))
            box.depth = env.fontsize * (1.0/3.0)
            box.height = env.fontsize - box.depth
            box.set_subj(node, 0)
            tokens.extend([box])
        else:
            tokens.extend(env.font(node, env.fontsize))
    return hpack(tokens + env.font(" [flat]", env.fontsize, color=env.blue))

def clamp(x, low, high):
    return min(max(x, low), high)

def get_window_size():
    width = c_int()
    height = c_int()
    SDL_GetWindowSize(window, byref(width), byref(height))
    return width.value, height.value

if __name__=='__main__':
    init()
    main(lambda: None)
