from boxmodel import *
from compositor import Compositor
from ctypes import c_int, byref, c_char, POINTER, c_void_p
from newdom import Document, Group, Symbol
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
    global window, context, images, back, middle, front, document, env, head, tail
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

    back = Compositor(images)
    middle = Compositor(images)
    front = Compositor(images)


    s0 = Symbol("")
    s1 = Symbol("")
    s5 = Symbol("")
    s2 = Symbol("")
    s3 = Symbol("")
    document = Document([s0, s1, s5, s2, s3])

    Group('xor', [s1, s5])
    a2 = Group('and', [s0, s2])
    a3 = Group('or', [a2, s3])

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
    global head, tail
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
                if key == 'f10':
                    syms = [Symbol(""), Symbol("")]
                    Group("+test+", syms)
                    document.put(head.pos+1, syms)
                if key == 'f12':
                    back.debug = not back.debug
                    middle.debug = not middle.debug
                    front.debug = not front.debug
                if key == 'space':
                    symbol = document[head.pos]
                    document.put(head.pos+1, [Symbol(symbol.drop(head.index, len(symbol)))])
                    head = Position(head.pos+1, 0)
                    tail = head
                elif text is not None:
                    symbol = document[head.pos]
                    symbol.put(head.index, text)
                    head = Position(head.pos, head.index + len(text))
                    tail = head
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
    back.clear()
    middle.clear()
    front.clear()

    rootbox = layout(document, 0, len(document))
    back.compose(rootbox, 10, 50)

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

    back.render(0, 0, width, height)
    middle.render(0, 0, width, height)
    front.render(0, 0, width, height)

def layout(document, start, stop):
    tokens = []
    ctx = Object(document=document, index=start)
    while ctx.index < stop:
        if len(tokens) > 0:
            tokens.extend(env.font(' ', env.fontsize))
        node = document[ctx.index]
        tokens.extend(layout_node(node.root, ctx))
    return hpack(tokens)

def layout_node(node, ctx):
    if isinstance(node, Symbol):
        if ctx.index < node.index:
            start, stop = ctx.index, node.index
            outbox = wrap_outbox(document, ctx.index, node.index)
        else:
            outbox = lambda b: b
        ctx.index = node.index + 1
    if isinstance(node, Group):
        tokens = []
        for subnode in node:
            if len(tokens) > 0:
                tokens.extend(env.font(' {} '.format(node.schema), env.fontsize, color=env.blue))
            tokens.append(hpack(layout_node(subnode, ctx)))
        return [hpack(tokens)]
    elif isinstance(node, Symbol) and len(node) == 0:
        box = hpack(env.font("___", env.fontsize, color=env.blue))
        box.depth = env.fontsize * (1.0/3.0)
        box.height = env.fontsize - box.depth
        box.set_subj(node, 0)
        return outbox([box])
    else:
        return outbox([hpack(env.font(node, env.fontsize))])

def wrap_outbox(document, start, stop):
    outbox = layout(document, start, stop)
    def _impl_(tokens):
        block = hpack([ImageBox(5, 20, 5, None, color=(1, 1, 1, 0.1)), Glue(4)] + tokens)
        vbox = vpack([Padding(outbox, (5, 5, 5, 5), color=(1, 1, 1, 0.1)), Glue(0), block])
        vsize = vbox.vsize
        vbox.depth = block.depth
        vbox.height = vsize - vbox.depth
        vbox.width = block.width
        return [vbox]
    return _impl_


def hinted(seq, hint):
    for item in seq:
        item.hint = hint
    return seq

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
