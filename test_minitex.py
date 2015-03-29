from compositor import Compositor
from ctypes import byref
from minitex import *
from OpenGL.GL import *
from sdl2 import *
import font
import sdl_backend
import time

def main(respond):
    global window, compositor, env
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
    compositor = Compositor(images)
    env = Environ.root(dict(
        font=font.load("OpenSans.fnt"),
        font_size=16,
        color=(0, 0, 0, 1.0)))
    keyboard = sdl_backend.KeyboardStream()
    event = SDL_Event()
    running = True
    while running:
        respond()
        while SDL_PollEvent(byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
            elif event.type == SDL_MOUSEBUTTONDOWN:
                compositor.debug = not compositor.debug
            else:
                pass #keyboard.push_event(event)
        paint(time.time())
        SDL_GL_SwapWindow(window)


def paint(t):
    width, height = sdl_backend.get_window_size(window)
    glViewport(0, 0, width, height)

    glClearColor(0.8, 0.8, 0.7, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    compositor.clear()
    box = toplevel(page(), env, dict(page_width=width-20, line_break=line_break))
    compositor.compose(box, 10, box.height + 10)
    compositor.render(0, 0, width, height)

def rjust(cell):
    return scope([hfil, cell])

def codeline(contents):
    def _codeline(env):
        env = Environ.let(env, {'depth': env.depth+1})
        if env.depth > 1:
            for item in contents:
                for box in fold(item, env):
                    yield box
        else:
            row = []
            for item in contents:
                row.extend(fold(item, env))
            boxes = list(codeline_break(env.page_width, row, 0))
            yield vpack(boxes)
    return _codeline

def codeline_break(width, row, indent):
    remaining = width
    best_depth = 10000
    for box in row:
        remaining -= box.width
        #if remaining < 0:
        best_depth = min(
            best_depth,
            box.get_hint('break_depth', 10000))
    if best_depth >= 10000 or remaining > 0:
        line = hpack(row)
        line.shift = indent
        yield line
    else:
        res, shift = [], 0
        for box in row:
            if box.get_hint('break_depth') == best_depth:
                for subline in codeline_break(width-shift, res, indent+shift):
                    yield subline
                res, shift = [], 40
            else:
                res.append(box)
        for subline in codeline_break(width-shift, res, indent+shift):
            yield subline

def nl(env):
    k = Glue(0)
    k.hint = {'break_depth': env.depth}
    yield k

def page():
    return [
        codeline([
            "foobar(", nl, codeline(["blark(", nl,
                codeline(["hello(", nl, "hell0, ", nl, "hello, ", nl, "hey)"]),
                ", ", nl,
                "blaa bla a blaa",
                ", ", nl,
                codeline(["hello(", nl, "hell0, ", nl, "hello, ", nl, "hey)"]),
                ", ", nl,
                codeline(["hello(", nl, "hell0, ", nl, "hello, ", nl, "hey)"]),
                ")"
            ]), ")"
        ])
    ]
    return [
        scope([
            "OpenGL rendered by test_minitex.py [~100 lines] in: ",
            "http://github.com/cheery/textended-edit/",
        ], dict(font_size=8)),
        par,
        "Hi there, We have not been properly introduced, but I already know your name. You're the ",
        scope(["AMAZING Spiderman"], dict(font_size=20)), ". I am pleased to meet you!",
        par,
        scope(["- Bonzi (Buddy) Savage"], dict(font_size=10, color=(0.4, 0, 0, 1))),
        par,
        "Serious matrices: ",
        table([
            map(rjust, ["1.0,", " 15.0,", " 0.0"]),
            map(rjust, ["0.0,", " 1.0,", " 0.0"]),
            map(rjust, ["0.0,", " 0.0,", " 1.0"]),
            map(rjust, ["23.0,", " 44.0,", " -5.0"]),
        ]),
        " and.. ",
        table([
            map(rjust, ["1.0,", " 15.0,", " 0.0"]),
            map(rjust, ["0.0,", " 1.0,", " 0.0"]),
            map(rjust, ["0.0,", " 0.0,", " 1.0"]),
        ]),
        par,
        vbox([
            scope([par, par, "Why? What?"], dict(font_size=20)), par,
            "I need to display some structures in my editor. "
            "But I needed configurable layout. "
            "I designed combinators that imitate at "
            "a famous typesetting system TeX. "
        ], dict(font_size=11, page_width=400, text_align=line_left))
    ]

if __name__=='__main__':
    main(lambda: None)
