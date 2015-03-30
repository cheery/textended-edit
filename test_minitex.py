from compositor import Compositor
from minitex import *
from minitex import font
from OpenGL.GL import *
import sdlut
import time
import os

def main(respond):
    global screen, compositor, env
    basedir = os.path.dirname(os.path.abspath(__file__))
    screen = sdlut.Screen("text here", 640, 480)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    images = sdlut.ImageResources()
    compositor = Compositor(images)
    env = Environ.root(dict(
        font=font.load(os.path.join(basedir, "assets/OpenSans.fnt")),
        font_size=16,
        color=(0, 0, 0, 1.0)))
    keyboard = sdlut.KeyboardStream()
    running = True
    while running:
        respond()
        for event in sdlut.poll_events():
            if event.type == sdlut.SDL_QUIT:
                running = False
            elif event.type == sdlut.SDL_MOUSEBUTTONDOWN:
                compositor.debug = not compositor.debug
            else:
                pass #keyboard.push_event(event)
        paint(screen, time.time())
        screen.swap()

def paint(screen, t):
    glViewport(0, 0, screen.width, screen.height)

    glClearColor(0.8, 0.8, 0.7, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    compositor.clear()
    box = toplevel(page(), env, dict(page_width=screen.width-20, line_break=line_break))
    compositor.compose(box, 10, box.height + 10)
    compositor.render(0, 0, screen.width, screen.height)

def rjust(cell):
    return scope([hfil, cell])

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
